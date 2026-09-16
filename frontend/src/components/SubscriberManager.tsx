import React, { useState, useEffect } from 'react';
import { Users, Copy, Check, Plus, Trash2, RotateCcw, ShieldCheck, UserPlus } from 'lucide-react';
import { apiGet, apiPost, apiDelete } from '../api/client';

export interface Subscriber {
  account_number: string;
  phone_number: string;
  customer_name: string;
  email?: string;
  zip_code: string;
  address: string;
  plan_name: string;
  monthly_rate: number;
  current_balance: number;
  due_date: string;
  router_status: string;
  has_active_outage: boolean;
}

const PLAN_OPTIONS = [
  { name: "GigaFiber 500 Ultra", rate: 80.0 },
  { name: "FiberConnect 300", rate: 65.0 },
  { name: "Gigabit Pro 1000", rate: 110.0 },
  { name: "FiberConnect 1000", rate: 95.0 },
  { name: "Basic Broadband 100", rate: 45.0 }
];

export const SubscriberManager: React.FC = () => {
  const [subscribers, setSubscribers] = useState<Subscriber[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'create' | 'quick'>('create');

  // Full User Creation Form State (Strictly Pure Numeric Account Numbers)
  const [accountNumber, setAccountNumber] = useState<string>('1006');
  const [customerName, setCustomerName] = useState<string>('');
  const [phoneNumber, setPhoneNumber] = useState<string>('+1555019');
  const [email, setEmail] = useState<string>('');
  const [zipCode, setZipCode] = useState<string>('94107');
  const [address, setAddress] = useState<string>('100 Silicon Way, San Francisco, CA');
  const [planName, setPlanName] = useState<string>('GigaFiber 500 Ultra');
  const [monthlyRate, setMonthlyRate] = useState<number>(80.0);
  const [currentBalance, setCurrentBalance] = useState<number>(0.0);
  const [routerStatus, setRouterStatus] = useState<string>('ONLINE');
  const [hasActiveOutage, setHasActiveOutage] = useState<boolean>(false);

  // Quick Register My Phone State
  const [myPhone, setMyPhone] = useState<string>('');
  const [myName, setMyName] = useState<string>('');
  const [myZip, setMyZip] = useState<string>('94107');

  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const getNextNumericAccount = (list: Subscriber[]): string => {
    const numericIds = list
      .map(s => parseInt(s.account_number.replace(/\D/g, ''), 10))
      .filter(n => !isNaN(n) && n >= 1000);
    return numericIds.length > 0 ? (Math.max(...numericIds) + 1).toString() : '1006';
  };

  const fetchSubscribers = async () => {
    try {
      setIsLoading(true);
      const data = await apiGet<Subscriber[]>('/api/admin/subscribers');
      if (Array.isArray(data)) {
        setSubscribers(data);
        const nextId = getNextNumericAccount(data);
        setAccountNumber(nextId);
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

  // Full User Creation Handler
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanAcc = accountNumber.replace(/\D/g, '').trim();
    if (!cleanAcc) {
      setNotification({ message: "Account number must contain digits only (e.g. 1006)", type: 'error' });
      return;
    }
    if (!customerName.trim()) {
      setNotification({ message: "Please provide a customer name.", type: 'error' });
      return;
    }

    try {
      setIsSubmitting(true);
      const cleanPhone = phoneNumber.trim().startsWith('+') ? phoneNumber.trim() : `+${phoneNumber.trim()}`;

      await apiPost('/api/admin/subscribers', {
        account_number: cleanAcc,
        phone_number: cleanPhone,
        customer_name: customerName.trim(),
        email: email.trim() || `${customerName.toLowerCase().replace(/\s+/g, '.')}@example.com`,
        zip_code: zipCode.trim() || "94107",
        address: address.trim() || "100 Telecom Way",
        plan_name: planName,
        monthly_rate: Number(monthlyRate) || 80.0,
        current_balance: Number(currentBalance) || 0.0,
        router_status: routerStatus,
        has_active_outage: hasActiveOutage
      });

      setNotification({
        message: `Subscriber #${cleanAcc} (${customerName}) created successfully! You can immediately verify by Account #${cleanAcc}, Name, Phone, Email, or Zip.`,
        type: 'success'
      });

      // Clear & set next ID
      setCustomerName('');
      setEmail('');
      setPhoneNumber('+1555019');
      setCurrentBalance(0.0);
      setHasActiveOutage(false);

      await fetchSubscribers();
      setTimeout(() => setNotification(null), 7000);
    } catch (err) {
      console.error('User creation failed:', err);
      setNotification({ message: "Failed to create subscriber profile. Please check console.", type: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick Register My Phone Handler
  const handleRegisterMyNumber = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!myPhone.trim() || !myName.trim()) return;

    try {
      setIsSubmitting(true);
      const nextAcc = getNextNumericAccount(subscribers);
      const formattedPhone = myPhone.trim().startsWith('+') ? myPhone.trim() : `+${myPhone.trim()}`;

      await apiPost('/api/admin/subscribers', {
        account_number: nextAcc,
        phone_number: formattedPhone,
        customer_name: myName.trim(),
        email: `${myName.toLowerCase().replace(/\s+/g, '.')}@example.com`,
        zip_code: myZip.trim() || "94107",
        address: "742 Evergreen Terrace",
        plan_name: "GigaFiber 500 Ultra",
        monthly_rate: 80.0,
        current_balance: 45.0,
        router_status: "ONLINE",
        has_active_outage: false
      });

      setNotification({
        message: `Registered ${myName} (${formattedPhone}) as Account #${nextAcc}! Next time you call, the AI recognizes you immediately.`,
        type: 'success'
      });
      setMyPhone('');
      setMyName('');
      await fetchSubscribers();
      setTimeout(() => setNotification(null), 7000);
    } catch (err) {
      console.error('Registration failed:', err);
      setNotification({ message: "Failed to register number.", type: 'error' });
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
      setNotification({ message: "Reset to default numeric seed accounts (1001 to 1005).", type: 'success' });
      setTimeout(() => setNotification(null), 4000);
    } catch (err) {
      console.error('Reseed failed:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab Switcher & Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
              <Users className="w-4 h-4 text-indigo-400" />
              <span>Subscriber Management & Test Profile Studio</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Create custom subscribers with <strong>pure numeric account IDs</strong> (e.g. 1001, 1006). All users are immediately queryable in the Voice softphone.
            </p>
          </div>

          {/* Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1 rounded-xl border border-slate-800 shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('create')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeTab === 'create'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Create New User</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('quick')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeTab === 'quick'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Quick Pair Phone</span>
            </button>
          </div>
        </div>

        {notification && (
          <div className={`mt-3 p-3 rounded-xl text-xs flex items-center space-x-2 border ${
            notification.type === 'success'
              ? 'bg-emerald-950/80 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/80 border-rose-800 text-rose-300'
          }`}>
            <Check className="w-4 h-4 shrink-0" />
            <span>{notification.message}</span>
          </div>
        )}

        {/* Form 1: Full New User Creation */}
        {activeTab === 'create' && (
          <form onSubmit={handleCreateUser} className="mt-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {/* Account Number (Pure Numeric Only) */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 flex items-center justify-between mb-1">
                  <span>Numeric Account # :</span>
                  <span className="text-[10px] text-indigo-400 font-mono">Numbers only</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    pattern="[0-9]*"
                    inputMode="numeric"
                    placeholder="e.g. 1006"
                    value={accountNumber}
                    onChange={(e) => setAccountNumber(e.target.value.replace(/\D/g, ''))}
                    className="w-full bg-slate-950 border border-indigo-500/60 rounded-xl p-2.5 text-xs text-indigo-200 font-mono font-bold focus:outline-none focus:border-indigo-400"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setAccountNumber(getNextNumericAccount(subscribers))}
                    className="absolute right-1.5 top-1.5 px-1.5 py-1 bg-indigo-900/60 hover:bg-indigo-800 text-[10px] text-indigo-200 rounded cursor-pointer"
                    title="Auto-suggest next number"
                  >
                    Next ID
                  </button>
                </div>
              </div>

              {/* Customer Name */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Customer Full Name:</label>
                <input
                  type="text"
                  placeholder="e.g. Alice Chen"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              {/* Phone Number */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Phone Number (ANI):</label>
                <input
                  type="tel"
                  placeholder="+15550198888"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              {/* Billing Zip */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Billing ZIP Code:</label>
                <input
                  type="text"
                  placeholder="94107"
                  value={zipCode}
                  onChange={(e) => setZipCode(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              {/* Email */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Email Address:</label>
                <input
                  type="email"
                  placeholder="alice@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Plan Name */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Broadband Plan:</label>
                <select
                  value={planName}
                  onChange={(e) => {
                    const sel = e.target.value;
                    setPlanName(sel);
                    const opt = PLAN_OPTIONS.find(p => p.name === sel);
                    if (opt) setMonthlyRate(opt.rate);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {PLAN_OPTIONS.map(p => (
                    <option key={p.name} value={p.name}>{p.name} (${p.rate}/mo)</option>
                  ))}
                </select>
              </div>

              {/* Current Balance */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Current Balance ($):</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={currentBalance}
                  onChange={(e) => setCurrentBalance(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Router Status */}
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">ONT / Router Status:</label>
                <select
                  value={routerStatus}
                  onChange={(e) => setRouterStatus(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="ONLINE">ONLINE (Normal)</option>
                  <option value="OFFLINE">OFFLINE (Los Red Light)</option>
                  <option value="DEGRADED">DEGRADED (High Latency/Packet Loss)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
              {/* Address */}
              <div className="sm:col-span-2">
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Physical Service Address:</label>
                <input
                  type="text"
                  placeholder="100 Silicon Way, San Francisco, CA"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Outage Toggle & Submit */}
              <div className="flex items-center space-x-3 pt-4">
                <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasActiveOutage}
                    onChange={(e) => setHasActiveOutage(e.target.checked)}
                    className="w-4 h-4 rounded text-rose-600 bg-slate-950 border-slate-700"
                  />
                  <span>Active Outage In Area</span>
                </label>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-lg shadow-indigo-950/40 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create User #{accountNumber}</span>
                </button>
              </div>
            </div>
          </form>
        )}

        {/* Form 2: Quick Pair Phone */}
        {activeTab === 'quick' && (
          <form onSubmit={handleRegisterMyNumber} className="mt-4 grid grid-cols-1 sm:grid-cols-4 gap-3">
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
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Pair & Create Account</span>
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Active Subscribers List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-300">
            <Users className="w-4 h-4 text-indigo-400" />
            <span>Registered Subscribers & Test Profiles ({subscribers.length})</span>
          </div>
          <button
            type="button"
            onClick={handleReseed}
            className="py-1 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs flex items-center space-x-1.5 transition-colors cursor-pointer"
            title="Reset to default seed accounts (1001-1005)"
          >
            <RotateCcw className="w-3 h-3 text-slate-400" />
            <span>Reseed Defaults (1001-1005)</span>
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
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-bold">
                        #{sub.account_number}
                      </span>
                      <h4 className="text-sm font-semibold text-slate-100">{sub.customer_name}</h4>
                    </div>
                    <div className="text-[11px] text-slate-400">{sub.plan_name} • ${sub.monthly_rate || 80}/mo</div>
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
                    {sub.has_active_outage && (
                      <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-rose-950 text-rose-400 border border-rose-800">
                        OUTAGE
                      </span>
                    )}
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

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  {/* Account Number */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[9px] text-slate-500 uppercase font-medium">Account ID</div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="font-mono text-indigo-300 font-semibold">{sub.account_number}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sub.account_number, `acc-${sub.account_number}`)}
                        className="text-slate-500 hover:text-slate-300 p-0.5 cursor-pointer"
                        title="Copy account ID"
                      >
                        {copiedKey === `acc-${sub.account_number}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Zip Code */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[9px] text-slate-500 uppercase font-medium">Billing Zip</div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="font-mono text-cyan-300 font-semibold">{sub.zip_code}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sub.zip_code, `zip-${sub.account_number}`)}
                        className="text-slate-500 hover:text-slate-300 p-0.5 cursor-pointer"
                        title="Copy zip code"
                      >
                        {copiedKey === `zip-${sub.account_number}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Phone Number */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[9px] text-slate-500 uppercase font-medium">Phone (ANI)</div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="font-mono text-slate-300 truncate">{sub.phone_number}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sub.phone_number, `phone-${sub.account_number}`)}
                        className="text-slate-500 hover:text-slate-300 p-0.5 cursor-pointer"
                        title="Copy phone"
                      >
                        {copiedKey === `phone-${sub.account_number}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Balance */}
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    <div className="text-[9px] text-slate-500 uppercase font-medium">Balance</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      ${Number(sub.current_balance).toFixed(2)}
                    </div>
                  </div>
                </div>

                {/* Spoken Utterance Quick Copy for Easy Testing */}
                <div className="pt-1 flex flex-wrap items-center gap-1.5 border-t border-slate-900">
                  <span className="text-[10px] text-slate-500">Quick Test Utterances:</span>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(`My account number is ${sub.account_number}.`, `utt-acc-${sub.account_number}`)}
                    className="px-2 py-0.5 rounded bg-slate-900 hover:bg-indigo-950/60 border border-slate-800 text-[10px] text-slate-400 hover:text-indigo-300 flex items-center space-x-1 cursor-pointer"
                  >
                    <span>"My account number is {sub.account_number}"</span>
                    {copiedKey === `utt-acc-${sub.account_number}` ? <Check className="w-2.5 h-2.5 text-emerald-400" /> : <Copy className="w-2.5 h-2.5" />}
                  </button>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(`My name is ${sub.customer_name}.`, `utt-name-${sub.account_number}`)}
                    className="px-2 py-0.5 rounded bg-slate-900 hover:bg-indigo-950/60 border border-slate-800 text-[10px] text-slate-400 hover:text-indigo-300 flex items-center space-x-1 cursor-pointer"
                  >
                    <span>"My name is {sub.customer_name}"</span>
                    {copiedKey === `utt-name-${sub.account_number}` ? <Check className="w-2.5 h-2.5 text-emerald-400" /> : <Copy className="w-2.5 h-2.5" />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

