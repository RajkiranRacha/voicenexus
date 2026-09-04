export interface NextBestAction {
  action: string;
  recommendation: string;
  tip: string;
}

/** Pure lookup, no I/O: suggests an agent-desktop next-best-action from the AI-prepared escalation context. */
export function getNextBestAction(intent: string, balance: number, reason: string): NextBestAction {
  if (reason.includes("OUT_OF_SCOPE") || reason.includes("DISPUTE")) {
    return {
      action: "Specialized Billing Review",
      recommendation: "Review line-item charges on latest invoice. Customer requested split-payment or fee dispute which requires manual adjustment override.",
      tip: "You have authority to issue a courtesy credit of up to $25 without supervisor sign-off."
    };
  }
  if (intent.includes("BILLING") || intent.includes("PAYMENT")) {
    return {
      action: "Payment Resolution & Autopay Enrollment",
      recommendation: `Customer balance is $${balance.toFixed(2)}. Offer 3-month split arrangement or $10 monthly discount for Autopay sign-up.`,
      tip: "Confirm payment promise in BSS to prevent automatic service suspension."
    };
  }
  if (intent.includes("OUTAGE")) {
    return {
      action: "Active Service Restoration Check",
      recommendation: "Regional fiber outage active. Inform customer repair crew is on-site with estimated restoration in 2 hours. Do NOT dispatch a truck.",
      tip: "Enroll customer in automated SMS restoration alerts."
    };
  }
  if (intent.includes("PLAN")) {
    return {
      action: "Loyalty Upgrade Offer",
      recommendation: "Eligible for Gigabit Pro 1000 promotion ($110/mo) with free Wi-Fi 6 gateway upgrade.",
      tip: "Mention 1-year price lock guarantee to close the upgrade."
    };
  }
  return {
    action: "Active Listening & Inquiry Clarification",
    recommendation: "Acknowledge the customer's previous turns in IVR. Confirm their primary issue directly without asking them to repeat basic information.",
    tip: "Customer identity has already been verified via VoiceNexus."
  };
}
