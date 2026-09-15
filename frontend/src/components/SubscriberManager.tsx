import React, { useState, useEffect } from 'react';
import { Users, Copy, Check, Plus, Trash2, RotateCcw, ShieldCheck } from 'lucide-react';
import { apiGet, apiPost, apiDelete } from '../api/client';

export interface Subscriber {
  account_number: string;
  phone_number: string;
  customer_name: string;
  zip_code: string;
  address: string;
  plan_name: string;
  monthly_rate: number;
  current_balance: number;
  due_date: string;
  router_status: string;
  has_active_outage: boolean;
}

export const SubscriberManager: React.FC = () => {
  const [subscribers, setSubscribers] = useState<Subscriber[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Quick Register Form State
  const [myPhone, setMyPhone] = useState<string>("");
  const [myName, setMyName] = useState<string>("");
  const [myZip, setMyZip] = useState<string>("94107");
  const [regSuccess, setRegSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fetchSubscribers = async () => {
    try {
      setIsLoading(true);
      const data = await apiGet<Subscriber[]>('/api/admin/subscribers');
      if (Array.isArray(data)) {
        setSubscribers(data);
      }
    } catch (e) {
      console.error('Failed to load subscribers:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscribers();
  }, []);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleRegisterMyNumber = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!myPhone.trim() || !myName.trim()) return;

    try {
      setIsSubmitting(true);
      const cleanDigits = myPhone.replace(/\D/g, '');
      const accNum = `ACC-${cleanDigits.slice(-4) || 'USER'}`;

      await apiPost('/api/admin/subscribers', {
        account_number: accNum,
        phone_number: myPhone.trim().startsWith('+') ? myPhone.trim() : `+${myPhone.trim()}`,
        customer_name: myName.trim(),
        zip_code: myZip.trim() || "94107",
        address: "742 Evergreen Terrace",
        plan_name: "GigaFiber 500 Ultra",
        monthly_rate: 80.0,
        current_balance: 45.0,
        router_status: "ONLINE",
        has_active_outage: false
      });

      setRegSuccess(`Successfully registered ${myName} (${myPhone})! Next time you call, the AI will recognize you immediately.`);
      setMyPhone("");
      setMyName("");
      fetchSubscribers();
      setTimeout(() => setRegSuccess(null), 6000);
    } catch (err) {
      console.error('Registration failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (accountNumber: string) => {
    try {
      await apiDelete(`/api/admin/subscribers/${accountNumber}`);
      fetchSubscribers();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const handleReseed = async () => {
    try {
      await apiPost('/api/admin/subscribers/seed');
      fetchSubscribers();
    } catch (err) {
      console.error('Reseed failed:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Quick Register My Number Card */}
      <div className="bg-gradient-to-r from-indigo-950/70 via-slate-900 to-slate-900 border border-indigo-800/60 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-indigo-300 pb-2 border-b border-indigo-900/60">
          <ShieldCheck className="w-4 h-4 text-indigo-400" />
          <span>Quick Register Your Own Phone Number (1-Click Test Pairing)</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Want the AI to recognize you by name when you call? Add your personal mobile number below.
          The AI will automatically identify your Caller ID (ANI) and skip asking for account verification!
        </p>

        {regSuccess && (
          <div className="p-3 bg-emerald-950/80 border border-emerald-800 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{regSuccess}</span>
          </div>
        )}

        <form onSubmit={handleRegisterMyNumber} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div>
            <label className="text-[11px] font-medium text-slate-300 block mb-1">Your Mobile Number (with country code):</label>
            <input
              type="text"
              placeholder="+919876543210 or +1555019..."
              value={myPhone}
              onChange={(e) => setMyPhone(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              required
            />
          </div>

          <div>
            <label className="text-[11px] font-medium text-slate-300 block mb-1">Your Full Name:</label>
            <input
              type="text"
              placeholder="e.g. Raj Kiran"
              value={myName}
              onChange={(e) => setMyName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div>
            <label className="text-[11px] font-medium text-slate-300 block mb-1">Billing Zip Code:</label>
            <input
              type="text"
              placeholder="94107"
              value={myZip}
              onChange={(e) => setMyZip(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-lg shadow-indigo-950/40 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Register My Number</span>
            </button>
          </div>
        </form>
      </div>

      {/* Active Subscribers List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400">
            <Users className="w-4 h-4 text-indigo-400" />
            <span>Registered Subscribers & Test Profiles ({subscribers.length})</span>
          </div>
          <button
            type="button"
            onClick={handleReseed}
            className="py-1 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs flex items-center space-x-1.5 transition-colors cursor-pointer"
            title="Reset to default seed accounts"
          >
            <RotateCcw className="w-3 h-3 text-slate-400" />
            <span>Reseed Defaults</span>
          </button>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading subscriber profiles...</div>
        ) : subscribers.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">No subscribers registered. Click Reseed Defaults above.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {subscribers.map((sub) => (
              <div
                key={sub.account_number}
                className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 relative group hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100">{sub.customer_name}</h4>
                    <span className="text-[11px] text-slate-400">{sub.plan_name}</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono border ${
                      sub.router_status === 'ONLINE'
                        ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                        : sub.router_status === 'OFFLINE'
                        ? 'bg-rose-950 text-rose-400 border-rose-800'
                        : 'bg-amber-950 text-amber-400 border-amber-800'
                    }`}>
                      {sub.router_status}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDelete(sub.account_number)}
                      className="text-slate-600 hover:text-rose-400 transition-colors p-1 cursor-pointer"
                      title="Delete profile"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  {/* Account Number */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-medium">Account ID</div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="font-mono text-indigo-300 font-semibold">{sub.account_number}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sub.account_number, `acc-${sub.account_number}`)}
                        className="text-slate-500 hover:text-slate-300 p-0.5"
                        title="Copy account ID"
                      >
                        {copiedKey === `acc-${sub.account_number}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Zip Code */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-medium">Billing Zip</div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="font-mono text-cyan-300 font-semibold">{sub.zip_code}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sub.zip_code, `zip-${sub.account_number}`)}
                        className="text-slate-500 hover:text-slate-300 p-0.5"
                        title="Copy zip code"
                      >
                        {copiedKey === `zip-${sub.account_number}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Phone Number */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-medium">Phone (ANI)</div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="font-mono text-slate-300">{sub.phone_number}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sub.phone_number, `phone-${sub.account_number}`)}
                        className="text-slate-500 hover:text-slate-300 p-0.5"
                        title="Copy phone"
                      >
                        {copiedKey === `phone-${sub.account_number}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Balance */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-medium">Balance</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      ${sub.current_balance.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
