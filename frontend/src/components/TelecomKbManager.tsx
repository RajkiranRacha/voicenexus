import React, { useState, useEffect } from 'react';
import {
  BookOpen, Plus, Search, Trash2, Upload, CheckCircle2,
  AlertCircle, Sparkles, RefreshCw, Globe, HelpCircle
} from 'lucide-react';
import { apiGet, apiPost, apiDelete } from '../api/client';

export interface KnowledgeArticle {
  id: string;
  topic: string;
  category: string;
  keywords: string[];
  questions: string[];
  answers: {
    en: string;
    es?: string;
    hi?: string;
  };
  action_type?: string;
}

export const TelecomKbManager: React.FC = () => {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [showImportModal, setShowImportModal] = useState<boolean>(false);
  const [importJsonText, setImportJsonText] = useState<string>('');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Test Simulator State
  const [testQuery, setTestQuery] = useState<string>('');
  const [testLang, setTestLang] = useState<string>('en-US');
  const [testResult, setTestResult] = useState<any>(null);
  const [isTesting, setIsTesting] = useState<boolean>(false);

  // New Article Form State
  const [newTopic, setNewTopic] = useState<string>('');
  const [newCategory, setNewCategory] = useState<string>('Device & SIM');
  const [newKeywords, setNewKeywords] = useState<string>('');
  const [newQuestions, setNewQuestions] = useState<string>('');
  const [newAnswerEn, setNewAnswerEn] = useState<string>('');
  const [newAnswerEs, setNewAnswerEs] = useState<string>('');
  const [newAnswerHi, setNewAnswerHi] = useState<string>('');

  const fetchArticles = async () => {
    setIsLoading(true);
    try {
      const data = await apiGet<KnowledgeArticle[]>('/api/admin/knowledge');
      setArticles(data);
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Failed to load knowledge base: ${err.message}` });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, []);

  const handleTestMatch = async () => {
    if (!testQuery.trim()) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await apiPost<any>('/api/admin/knowledge/test', {
        query: testQuery,
        language: testLang
      });
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ matched: false, message: `Error testing query: ${err.message}` });
    } finally {
      setIsTesting(false);
    }
  };

  const handleCreateArticle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTopic.trim() || !newAnswerEn.trim()) {
      setFeedback({ type: 'error', message: 'Topic and English answer are required.' });
      return;
    }

    const payload = {
      topic: newTopic.trim(),
      category: newCategory,
      keywords: newKeywords.split(',').map(k => k.trim()).filter(Boolean),
      questions: newQuestions.split('\n').map(q => q.trim()).filter(Boolean),
      answers: {
        en: newAnswerEn.trim(),
        ...(newAnswerEs.trim() ? { es: newAnswerEs.trim() } : {}),
        ...(newAnswerHi.trim() ? { hi: newAnswerHi.trim() } : {}),
      },
      action_type: 'RESOLVED_INFO'
    };

    try {
      await apiPost('/api/admin/knowledge', payload);
      setFeedback({ type: 'success', message: `Knowledge article "${newTopic}" created successfully!` });
      setShowAddModal(false);
      resetForm();
      fetchArticles();
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Error saving article: ${err.message}` });
    }
  };

  const resetForm = () => {
    setNewTopic('');
    setNewCategory('Device & SIM');
    setNewKeywords('');
    setNewQuestions('');
    setNewAnswerEn('');
    setNewAnswerEs('');
    setNewAnswerHi('');
  };

  const handleDelete = async (id: string, topic: string) => {
    if (!window.confirm(`Are you sure you want to delete "${topic}" from the AI knowledge base?`)) return;
    try {
      await apiDelete(`/api/admin/knowledge/${id}`);
      setFeedback({ type: 'success', message: `Deleted article "${topic}".` });
      fetchArticles();
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Failed to delete article: ${err.message}` });
    }
  };

  const handleImportJson = async () => {
    try {
      const parsed = JSON.parse(importJsonText);
      if (!Array.isArray(parsed)) {
        throw new Error("JSON must be an array of articles.");
      }
      const res: any = await apiPost('/api/admin/knowledge/import', { articles: parsed });
      setFeedback({ type: 'success', message: `Successfully imported ${res.imported_count || parsed.length} articles into the AI knowledge base!` });
      setShowImportModal(false);
      setImportJsonText('');
      fetchArticles();
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Import failed: ${err.message}` });
    }
  };

  const categories = ['ALL', ...Array.from(new Set(articles.map(a => a.category)))];

  const filteredArticles = articles.filter(art => {
    const matchCategory = selectedCategory === 'ALL' || art.category === selectedCategory;
    const matchSearch = !searchFilter.trim() ||
      art.topic.toLowerCase().includes(searchFilter.toLowerCase()) ||
      art.keywords.some(k => k.toLowerCase().includes(searchFilter.toLowerCase())) ||
      art.questions.some(q => q.toLowerCase().includes(searchFilter.toLowerCase()));
    return matchCategory && matchSearch;
  });

  return (
    <div className="space-y-6">
      {/* Alert Notification */}
      {feedback && (
        <div className={`p-3.5 rounded-xl text-xs flex items-center justify-between border ${
          feedback.type === 'success'
            ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
            : 'bg-rose-950/70 border-rose-800 text-rose-300'
        }`}>
          <div className="flex items-center space-x-2">
            {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertCircle className="w-4 h-4 text-rose-400" />}
            <span>{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-slate-400 hover:text-slate-200 cursor-pointer font-bold">×</button>
        </div>
      )}

      {/* Top Controls & Action Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-slate-400">
            <BookOpen className="w-4 h-4 text-indigo-400" />
            <span>Telecom Knowledge Base & AI Ingestion (Defect-2)</span>
          </div>
          <h3 className="text-base font-bold text-slate-100 mt-1">
            Active Domain Knowledge Articles ({articles.length})
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Train VoiceNexus on telco care topics (eSIM, Roaming, Router LEDs, Wi-Fi setup, MNP, APN).
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2">
          <button
            type="button"
            onClick={fetchArticles}
            disabled={isLoading}
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer"
            title="Reload Knowledge Base"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => setShowImportModal(true)}
            className="py-2.5 px-3.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium flex items-center space-x-1.5 border border-slate-700 transition-all cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5 text-indigo-400" />
            <span>Batch Import JSON</span>
          </button>

          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-indigo-950/40 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Knowledge Article</span>
          </button>
        </div>
      </div>

      {/* Interactive AI Query Match Tester */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Test Telecom AI Recognition (Live Simulation)</span>
          </span>
          <span className="text-[11px] text-slate-500">Test how the AI resolves customer questions</span>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleTestMatch()}
              placeholder="Ask a question (e.g., 'How do I activate eSIM on my phone?' or 'router light is blinking red')..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <select
            value={testLang}
            onChange={(e) => setTestLang(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="en-US">English (en-US)</option>
            <option value="es-US">Español (es-US)</option>
            <option value="hi-IN">Hindi (hi-IN)</option>
          </select>

          <button
            type="button"
            onClick={handleTestMatch}
            disabled={isTesting || !testQuery.trim()}
            className="py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold rounded-xl flex items-center justify-center space-x-1.5 transition-all cursor-pointer"
          >
            {isTesting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
            <span>Test Match</span>
          </button>
        </div>

        {/* Test Result Display */}
        {testResult && (
          <div className={`mt-2 p-3.5 rounded-xl border text-xs ${
            testResult.matched
              ? 'bg-indigo-950/40 border-indigo-800 text-slate-200'
              : 'bg-slate-950 border-slate-800 text-slate-400'
          }`}>
            {testResult.matched ? (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-indigo-300 flex items-center space-x-2">
                    <span>Matched Topic: {testResult.topic}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-900/80 text-indigo-200 border border-indigo-700">
                      Category: {testResult.category}
                    </span>
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                    Confidence: {(testResult.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="text-slate-300 text-xs bg-slate-900/90 p-3 rounded-lg border border-slate-800 mt-1">
                  <strong>AI Response:</strong> "{testResult.answer}"
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-slate-400">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <span>{testResult.message}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Category Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 max-w-full">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-slate-900 hover:bg-slate-850 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Filter Input */}
        <div className="relative min-w-[220px]">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search keywords, topics..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-8 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredArticles.map((art) => (
          <div key={art.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between space-y-3 hover:border-slate-700 transition-all">
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-950 text-indigo-300 border border-slate-800">
                    {art.category}
                  </span>
                  <h4 className="text-sm font-bold text-slate-100 mt-1.5">{art.topic}</h4>
                </div>
                <button
                  onClick={() => handleDelete(art.id, art.topic)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors cursor-pointer"
                  title="Delete article"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Keywords */}
              <div className="flex flex-wrap gap-1 mb-2.5">
                {art.keywords.slice(0, 6).map((kw, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800/80 font-mono">
                    {kw}
                  </span>
                ))}
                {art.keywords.length > 6 && (
                  <span className="text-[10px] px-1.5 py-0.5 text-slate-500 font-mono">
                    +{art.keywords.length - 6} more
                  </span>
                )}
              </div>

              {/* English Response Preview */}
              <div className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-slate-800/60 line-clamp-3">
                <span className="text-indigo-400 font-semibold mr-1">EN:</span>
                "{art.answers.en}"
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
              <div className="flex items-center space-x-2">
                <Globe className="w-3 h-3 text-cyan-400" />
                <span>Languages: EN {art.answers.es ? '· ES' : ''} {art.answers.hi ? '· HI' : ''}</span>
              </div>
              <span>{art.questions.length} sample queries</span>
            </div>
          </div>
        ))}
      </div>

      {/* Guide: How to Feed Data to VoiceNexus */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 text-xs text-slate-400 space-y-2">
        <h4 className="font-bold text-slate-200 flex items-center space-x-2">
          <HelpCircle className="w-4 h-4 text-indigo-400" />
          <span>How to Feed Telecom Data to the VoiceNexus AI Assistant</span>
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/60">
            <strong className="text-indigo-300 block mb-1">1. Web UI Ingestion (Instant)</strong>
            Click <strong>New Knowledge Article</strong> above to immediately save a topic with keywords and localized answers. Live instantly with zero server restarts.
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/60">
            <strong className="text-indigo-300 block mb-1">2. Batch JSON File Upload</strong>
            Use <strong>Batch Import JSON</strong> to upload collections of telecom FAQs or export files from Zendesk, Salesforce, or ServiceNow knowledge bases.
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/60">
            <strong className="text-indigo-300 block mb-1">3. File / REST API Ingestion</strong>
            Directly edit <code className="text-indigo-400">backend/data/telecom_kb.json</code> or send <code className="text-indigo-400">POST /api/admin/knowledge</code> from your CI/CD or CRM pipeline.
          </div>
        </div>
      </div>

      {/* Modal: Add New Knowledge Article */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <Plus className="w-5 h-5 text-indigo-400" />
                <span>Add New Telecom Knowledge Article</span>
              </h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-200 cursor-pointer font-bold text-lg">×</button>
            </div>

            <form onSubmit={handleCreateArticle} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-medium text-slate-300 mb-1">Topic Title *:</label>
                <input
                  type="text"
                  required
                  value={newTopic}
                  onChange={(e) => setNewTopic(e.target.value)}
                  placeholder="e.g., 5G Roaming Setup in Europe"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Category:</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="Device & SIM">Device & SIM</option>
                  <option value="Roaming & Travel">Roaming & Travel</option>
                  <option value="Wi-Fi & Broadband">Wi-Fi & Broadband</option>
                  <option value="Equipment & Hardware">Equipment & Hardware</option>
                  <option value="Account & Porting">Account & Porting</option>
                  <option value="Billing & Payments">Billing & Payments</option>
                  <option value="General Support">General Support</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Keywords (comma-separated triggers) *:</label>
                <input
                  type="text"
                  required
                  value={newKeywords}
                  onChange={(e) => setNewKeywords(e.target.value)}
                  placeholder="e.g., europe roaming, travel pass, overseas 5g, data in paris"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Sample Questions (one per line):</label>
                <textarea
                  rows={2}
                  value={newQuestions}
                  onChange={(e) => setNewQuestions(e.target.value)}
                  placeholder="How do I use my phone in Europe?&#10;What is the international day pass cost?"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">English Spoken Answer * (Keep concise for voice):</label>
                <textarea
                  rows={3}
                  required
                  value={newAnswerEn}
                  onChange={(e) => setNewAnswerEn(e.target.value)}
                  placeholder="NexusFiber offers the Global Day Pass for $10/day. Turn on Data Roaming before traveling. Can I help you with anything else today?"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Spanish Answer (Español, optional):</label>
                <textarea
                  rows={2}
                  value={newAnswerEs}
                  onChange={(e) => setNewAnswerEs(e.target.value)}
                  placeholder="NexusFiber ofrece el pase diario de $10 al día. ¿Puedo ayudarle con algo más hoy?"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Hindi Answer (हिन्दी, optional):</label>
                <textarea
                  rows={2}
                  value={newAnswerHi}
                  onChange={(e) => setNewAnswerHi(e.target.value)}
                  placeholder="NexusFiber $10 प्रति दिन में ग्लोबल पास प्रदान करता है। क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Save to Knowledge Base
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Batch Import JSON */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <Upload className="w-5 h-5 text-indigo-400" />
                <span>Batch Import Telecom Knowledge (JSON)</span>
              </h3>
              <button onClick={() => setShowImportModal(false)} className="text-slate-400 hover:text-slate-200 cursor-pointer font-bold text-lg">×</button>
            </div>

            <div className="space-y-2 text-xs">
              <p className="text-slate-400">
                Paste a JSON array containing knowledge objects with <code className="text-indigo-400">topic</code>, <code className="text-indigo-400">keywords</code>, and <code className="text-indigo-400">answers</code>:
              </p>
              <textarea
                rows={8}
                value={importJsonText}
                onChange={(e) => setImportJsonText(e.target.value)}
                placeholder='[{"topic": "5G APN", "keywords": ["apn", "5g"], "answers": {"en": "Set APN to broadband.nexusfiber.net"}}]'
                className="w-full font-mono bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowImportModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleImportJson}
                disabled={!importJsonText.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl text-xs font-semibold cursor-pointer"
              >
                Import Articles
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
