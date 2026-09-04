import { useRef, useState, useCallback } from 'react';

interface UseWebRTCPeerOptions {
  onIceCandidate: (candidate: RTCIceCandidateInit) => void;
  onRemoteStream: (stream: MediaStream) => void;
}

/**
 * Shared WebRTC peer-connection plumbing used by both the caller phone
 * (answerer role: answers an offer relayed from the agent) and the agent
 * desktop (offerer role: originates the offer once a call is accepted).
 * Consolidates the RTCPeerConnection/STUN/track/ICE setup that was
 * previously duplicated between PhoneSimulator and AgentDesktop.
 */
export function useWebRTCPeer({ onIceCandidate, onRemoteStream }: UseWebRTCPeerOptions) {
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isMicActive, setIsMicActive] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);

  const ensurePeerConnection = useCallback((): RTCPeerConnection => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });
    pc.ontrack = (event) => {
      if (event.streams[0]) {
        onRemoteStream(event.streams[0]);
      }
    };
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        onIceCandidate(event.candidate.toJSON());
      }
    };
    pcRef.current = pc;
    return pc;
  }, [onIceCandidate, onRemoteStream]);

  const captureMicrophone = useCallback(async (): Promise<MediaStream | null> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
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
      stream.getAudioTracks().forEach(track => pc.addTrack(track, stream));
    } else {
      pc.addTransceiver('audio', { direction: 'recvonly' });
    }
  };

  /** Offerer role (agent desktop): capture mic, create + set local offer. */
  const createOffer = useCallback(async (): Promise<RTCSessionDescriptionInit> => {
    const stream = await captureMicrophone();
    const pc = ensurePeerConnection();
    attachLocalAudio(pc, stream);
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    return offer;
  }, [captureMicrophone, ensurePeerConnection]);

  /** Answerer role (caller phone): capture mic, answer a received offer. */
  const answerOffer = useCallback(async (sdpOffer: RTCSessionDescriptionInit): Promise<RTCSessionDescriptionInit> => {
    const stream = await captureMicrophone();
    const pc = ensurePeerConnection();
    attachLocalAudio(pc, stream);
    await pc.setRemoteDescription(new RTCSessionDescription(sdpOffer));
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    return answer;
  }, [captureMicrophone, ensurePeerConnection]);

  const setRemoteAnswer = useCallback(async (sdpAnswer: RTCSessionDescriptionInit) => {
    if (pcRef.current) {
      await pcRef.current.setRemoteDescription(new RTCSessionDescription(sdpAnswer));
    }
  }, []);

  const addRemoteIceCandidate = useCallback(async (candidate: RTCIceCandidateInit) => {
    if (pcRef.current) {
      try {
        await pcRef.current.addIceCandidate(new RTCIceCandidate(candidate));
      } catch {
        // ignore duplicate/late candidates
      }
    }
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
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    pcRef.current?.close();
    pcRef.current = null;
    setIsMicActive(false);
  }, []);

  return {
    isMicActive, isMuted, micError,
    createOffer, answerOffer, setRemoteAnswer, addRemoteIceCandidate,
    toggleMute, close,
  };
}
