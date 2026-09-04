export const PRESET_CALLERS = [
  {
    name: "Jordan Rivera",
    ani: "+15550192834",
    scenario: "Billing balance ($142.50), card on file, payment promise"
  },
  {
    name: "Elena Vance",
    ani: "+15550148821",
    scenario: "Seattle Metro area broadband outage"
  },
  {
    name: "Marcus Brody",
    ani: "+15550173399",
    scenario: "Degraded Wi-Fi gateway / packet loss triage"
  },
  {
    name: "Unregistered Caller (Unknown ANI)",
    ani: "+15559990000",
    scenario: "Requires KBA Auth (Account # or Zip code 94107)"
  }
];

export const PRESET_UTTERANCES = [
  { label: "Pay Bill Now (Card on File)", text: "I want to pay my bill now using the card on file." },
  { label: "Confirm Card Payment", text: "Yes, please charge my card." },
  { label: "Check Balance & Pay Next Week", text: "How much is my bill and can I set up a payment arrangement for next Friday?" },
  { label: "KBA Auth: Verify Zip 94107", text: "My billing zip code is 94107." },
  { label: "Bilingual: Switch to Spanish", text: "Quiero hablar en español." },
  { label: "Bilingual: Switch to English", text: "Please switch back to English." },
  { label: "Pronunciation: ONT & VoIP Status", text: "What is my ONT and VoIP speed status?" },
  { label: "Check Internet Outage", text: "My internet connection is completely down." },
  { label: "Opt-in to SMS Outage Alerts", text: "Yes, please enroll me in text alerts." },
  { label: "Approve Router Reboot", text: "Yes, go ahead and send the reset signal to reboot my router." },
  { label: "Inquire Plan & Upgrade", text: "What plan am I on and can I upgrade to gigabit speed?" },
  { label: "Schedule a Callback", text: "I'd like to schedule a callback for tomorrow morning." },
  { label: "Explicit Agent Request", text: "I need to speak to a human representative right now." }
];
