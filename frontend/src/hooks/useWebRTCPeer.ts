import { useRef, useState, useCallback } from 'react';

export const DEFAULT_ICE_SERVERS: RTCIceServer[] = [
  {
    urls: [
      'stun:stun.l.google.com:19302',
      'stun:stun1.l.google.com:19302',
      'stun:stun2.l.google.com:19302',
      'stun:stun.cloudflare.com:3478'
    ]
  }
];

interface UseWebRTCPeerOptions {
  onIceCandidate: (candidate: RTCIceCandidateInit) => void;
  onRemoteStream: (stream: MediaStream) => void;
  iceServers?: RTCIceServer[];
  onConnectionStateChange?: (state: RTCPeerConnectionState) => void;
}

/**
 * Shared WebRTC peer-connection plumbing used by both the caller phone
 * (answerer role: answers an offer relayed from the agent) and the agent
 * desktop (offerer role: originates the offer once a call is accepted).
 *
 * Provides:
 * - Redundant STUN + TURN NAT traversal
 * - Buffered ICE candidate queue preventing race-condition candidate drops
 * - Robust track & stream extraction for all browsers
 * - Real-time connection & ICE lifecycle states
 */
export function useWebRTCPeer({
  onIceCandidate,
  onRemoteStream,
  iceServers,
  onConnectionStateChange
}: UseWebRTCPeerOptions) {
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const pendingCandidatesRef = useRef<RTCIceCandidateInit[]>([]);

  const [isMicActive, setIsMicActive] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<RTCPeerConnectionState>('new');
  const [iceConnectionState, setIceConnectionState] = useState<RTCIceConnectionState>('new');

  const flushPendingCandidates = useCallback(async (pc: RTCPeerConnection) => {
    if (pendingCandidatesRef.current.length === 0) return;
    const candidates = [...pendingCandidatesRef.current];
    pendingCandidatesRef.current = [];
    for (const cand of candidates) {
      try {
        await pc.addIceCandidate(new RTCIceCandidate(cand));
      } catch (err) {
        console.warn('[WebRTC] Error adding buffered ICE candidate:', err);
      }
    }
  }, []);

  const ensurePeerConnection = useCallback((): RTCPeerConnection => {
    if (pcRef.current && pcRef.current.signalingState !== 'closed') {
      return pcRef.current;
    }

    const config: RTCConfiguration = {
      iceServers: iceServers && iceServers.length > 0 ? iceServers : DEFAULT_ICE_SERVERS,
      iceCandidatePoolSize: 2
    };

    const pc = new RTCPeerConnection(config);

    pc.ontrack = (event) => {
      // Robust stream resolution: Some browsers/negotiations don't populate
      // event.streams[0], so synthesize a stream from event.track if needed.
      const remoteStream = (event.streams && event.streams[0])
        ? event.streams[0]
        : new MediaStream([event.track]);
      onRemoteStream(remoteStream);
    };

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        onIceCandidate(event.candidate.toJSON());
      }
    };

    pc.onconnectionstatechange = () => {
      setConnectionState(pc.connectionState);
      onConnectionStateChange?.(pc.connectionState);
    };

    pc.oniceconnectionstatechange = () => {
      setIceConnectionState(pc.iceConnectionState);
    };

    pcRef.current = pc;
    return pc;
  }, [iceServers, onIceCandidate, onRemoteStream, onConnectionStateChange]);

  const captureMicrophone = useCallback(async (): Promise<MediaStream | null> => {
    // Reuse existing active media stream if available to prevent device re-prompting
    if (
      streamRef.current &&
      streamRef.current.active &&
      streamRef.current.getAudioTracks().some(t => t.readyState === 'live')
    ) {
      setIsMicActive(true);
      return streamRef.current;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      streamRef.current = stream;
      setIsMicActive(true);
      setIsMuted(false);
      setMicError(null);
      return stream;
    } catch (err: any) {
      setIsMicActive(false);
      setMicError(
        err?.name === 'NotAllowedError'
          ? "Microphone permission was denied by browser. Please allow microphone in browser settings to speak directly."
          : "No microphone device found. You can still transmit voice responses using quick speech."
      );
      return null;
    }
  }, []);

  /**
   * Adds the local mic track when available; otherwise explicitly negotiates
   * a recvonly audio transceiver. Without this, a peer connection that never
   * calls addTrack() (e.g. the agent's mic permission was denied/unavailable)
   * won't negotiate an audio m-line at all, silently breaking audio in BOTH
   * directions instead of just the side missing a microphone.
   */
  const attachLocalAudio = (pc: RTCPeerConnection, stream: MediaStream | null) => {
    if (stream) {
      const tracks = stream.getAudioTracks();
      // Check if tracks already added to pc
      const existingSenders = pc.getSenders();
      tracks.forEach(track => {
        const alreadyAdded = existingSenders.some(s => s.track === track);
        if (!alreadyAdded) {
          pc.addTrack(track, stream);
        }
      });
    } else {
      const transceivers = pc.getTransceivers();
      const hasAudio = transceivers.some(t => t.receiver.track.kind === 'audio');
      if (!hasAudio) {
        pc.addTransceiver('audio', { direction: 'recvonly' });
      }
    }
  };

  /** Offerer role (agent desktop): capture mic, create + set local offer. */
  const createOffer = useCallback(async (): Promise<RTCSessionDescriptionInit> => {
    const pc = ensurePeerConnection();
    const stream = await captureMicrophone();
    attachLocalAudio(pc, stream);
    const offer = await pc.createOffer({
      offerToReceiveAudio: true
    });
    await pc.setLocalDescription(offer);
    return offer;
  }, [captureMicrophone, ensurePeerConnection]);

  /** Answerer role (caller phone): answer received offer, capture mic, flush candidate queue. */
  const answerOffer = useCallback(async (sdpOffer: RTCSessionDescriptionInit): Promise<RTCSessionDescriptionInit> => {
    const pc = ensurePeerConnection();
    await pc.setRemoteDescription(new RTCSessionDescription(sdpOffer));

    // Flush any remote ICE candidates that arrived before setRemoteDescription
    await flushPendingCandidates(pc);

    const stream = await captureMicrophone();
    attachLocalAudio(pc, stream);

    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    return answer;
  }, [captureMicrophone, ensurePeerConnection, flushPendingCandidates]);

  const setRemoteAnswer = useCallback(async (sdpAnswer: RTCSessionDescriptionInit) => {
    if (pcRef.current) {
      await pcRef.current.setRemoteDescription(new RTCSessionDescription(sdpAnswer));
      // Flush any remote candidates received while awaiting answer
      await flushPendingCandidates(pcRef.current);
    }
  }, [flushPendingCandidates]);

  const addRemoteIceCandidate = useCallback(async (candidate: RTCIceCandidateInit) => {
    const pc = pcRef.current;
    // If peer connection or remoteDescription isn't set yet, buffer the candidate!
    if (!pc || !pc.remoteDescription || !pc.remoteDescription.type) {
      pendingCandidatesRef.current.push(candidate);
      return;
    }

    try {
      await pc.addIceCandidate(new RTCIceCandidate(candidate));
    } catch (err) {
      console.warn('[WebRTC] Error adding ICE candidate:', err);
    }
  }, []);

  const restartIce = useCallback(async (): Promise<RTCSessionDescriptionInit | null> => {
    const pc = pcRef.current;
    if (pc && typeof pc.restartIce === 'function') {
      pc.restartIce();
      const offer = await pc.createOffer({ iceRestart: true });
      await pc.setLocalDescription(offer);
      return offer;
    }
    return null;
  }, []);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => {
      if (!streamRef.current) return prev;
      const next = !prev;
      streamRef.current.getAudioTracks().forEach(track => { track.enabled = !next; });
      return next;
    });
  }, []);

  const close = useCallback(() => {
    pendingCandidatesRef.current = [];
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    pcRef.current?.close();
    pcRef.current = null;
    setIsMicActive(false);
    setConnectionState('closed');
    setIceConnectionState('closed');
  }, []);

  return {
    isMicActive,
    isMuted,
    micError,
    connectionState,
    iceConnectionState,
    captureMicrophone,
    createOffer,
    answerOffer,
    setRemoteAnswer,
    addRemoteIceCandidate,
    restartIce,
    toggleMute,
    close,
  };
}
