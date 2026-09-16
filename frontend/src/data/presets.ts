export const PRESET_CALLERS = [
  {
    name: "Jordan Rivera",
    ani: "+15550192834",
    scenario: "Acc: 1001 | Zip: 94107 | $142.50 balance | Online"
  },
  {
    name: "Elena Vance",
    ani: "+15550148821",
    scenario: "Acc: 1002 | Zip: 98101 | Active outage in Seattle | Offline"
  },
  {
    name: "Marcus Brody",
    ani: "+15550173399",
    scenario: "Acc: 1003 | Zip: 78701 | $220.00 past due | Degraded Wi-Fi"
  },
  {
    name: "Sam Taylor",
    ani: "+15550101001",
    scenario: "Acc: 1004 | Zip: 90210 | $45.00 balance | Pure numeric account"
  },
  {
    name: "Alex Morgan",
    ani: "+15550102002",
    scenario: "Acc: 1005 | Zip: 10001 | $0.00 balance | Fiber 1000 plan"
  },
  {
    name: "Unregistered Caller (Unknown ANI)",
    ani: "+15559990000",
    scenario: "Unknown caller - test finding account by Name, Email, Phone, Zip, or Acc # (1001-1005)"
  }
];

export const PRESET_UTTERANCES = [
  { label: "Auth: By Name (Jordan Rivera)", text: "My name is Jordan Rivera." },
  { label: "Auth: By Account (1001 - Jordan)", text: "My account number is 1001." },
  { label: "Auth: By Account (1002 - Elena)", text: "My account number is 1002." },
  { label: "Auth: By Account (1003 - Marcus)", text: "My account number is 1003." },
  { label: "Auth: By Phone (555-014-8821)", text: "My phone number is 555-014-8821." },
  { label: "Auth: By Email (sam.taylor@example.com)", text: "My email is sam.taylor@example.com." },
  { label: "Auth: By Zip Code (94107)", text: "My billing zip code is 94107." },
  { label: "Pay Bill Now (Card on File)", text: "I want to pay my bill now using the card on file." },
  { label: "Confirm Card Payment", text: "Yes, please charge my card." },
  { label: "Check Balance & Pay Next Week", text: "How much is my bill and can I set up a payment arrangement for next Friday?" },
  { label: "Bilingual: Switch to Spanish", text: "Quiero hablar en español." },
  { label: "Bilingual: Switch to English", text: "Please switch back to English." },
  { label: "Pronunciation: ONT & VoIP Status", text: "What is my ONT and VoIP speed status?" },
  { label: "Check Internet Outage", text: "My internet connection is completely down." },
  { label: "Opt-in to SMS Outage Alerts", text: "Yes, please enroll me in text alerts." },
  { label: "Approve Router Reboot", text: "Yes, go ahead and send the reset signal to reboot my router." },
  { label: "Inquire Plan & Upgrade", text: "What plan am I on and can I upgrade to gigabit speed?" },
  { label: "Schedule a Callback", text: "I'd like to schedule a callback for tomorrow morning." },
  { label: "Wrap-Up: No, Thanks for resolving", text: "No, Thanks for resolving" },
  { label: "Wrap-Up: Good to drop now", text: "There is no more concerns good to drop now" },
  { label: "Telecom KB: Activate eSIM", text: "How do I activate eSIM on my phone?" },
  { label: "Telecom KB: Router Blinking Red", text: "Why is the red LOS light blinking on my router?" },
  { label: "Telecom KB: Roaming Pass", text: "What roaming pass do I need while traveling abroad?" },
  { label: "Telecom KB: Number Porting (MNP)", text: "How do I get a transfer PIN to port my number?" },
  { label: "Explicit Agent Request", text: "I need to speak to a human representative right now." }
];
