import { useState } from 'react';
import { Brain, Send, BarChart3, Users, TrendingUp, DollarSign, FileText, Sparkles, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import api from '@/api/client';

const AI_FEATURES = [
  { id: 'chat', label: 'مساعد المحادثة', icon: Brain, color: 'from-blue-500 to-indigo-600', desc: 'اسأل أي سؤال عن التطبيق والبيانات' },
  { id: 'report', label: 'تحليل التقارير', icon: BarChart3, color: 'from-emerald-500 to-teal-600', desc: 'تحليل شامل مع توصيات' },
  { id: 'absence', label: 'تنبؤ الغياب', icon: TrendingUp, color: 'from-orange-500 to-red-600', desc: 'تحليل أنماط الغياب والتنبؤ' },
  { id: 'evaluation', label: 'تقييم الأداء', icon: Users, color: 'from-purple-500 to-pink-600', desc: 'ملخص تقييم أداء احترافي' },
  { id: 'financial', label: 'كشف الشذوذ المالي', icon: DollarSign, color: 'from-yellow-500 to-amber-600', desc: 'اكتشاف المعاملات المشبوهة' },
];

export default function AIAssistantPage() {
  const [activeFeature, setActiveFeature] = useState('chat');
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [reportType, setReportType] = useState('general');

  const handleChat = async () => {
    if (!chatMessage.trim() || loading) return;
    const msg = chatMessage.trim();
    setChatHistory(prev => [...prev, { role: 'user', content: msg }]);
    setChatMessage('');
    setLoading(true);
    try {
      const res = await api.post('/ai/chat', { message: msg });
      setChatHistory(prev => [...prev, { role: 'ai', content: res.data.data.reply }]);
    } catch (err: any) {
      setChatHistory(prev => [...prev, { role: 'ai', content: err.response?.data?.message || 'حدث خطأ' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (type: string) => {
    setLoading(true);
    setResult('');
    try {
      let res;
      switch (type) {
        case 'report':
          res = await api.post('/ai/report-analysis', { type: reportType });
          setResult(res.data.data.analysis);
          break;
        case 'absence':
          res = await api.post('/ai/attendance-prediction', {});
          setResult(res.data.data.prediction);
          break;
        case 'evaluation':
          res = await api.post('/ai/evaluation-review', {});
          setResult(res.data.data.review);
          break;
        case 'financial':
          res = await api.post('/ai/financial-anomaly', {});
          setResult(res.data.data.report);
          break;
      }
    } catch (err: any) {
      setResult(err.response?.data?.message || 'حدث خطأ في التحليل');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">المساعد الذكي</h1>
          <p className="text-gray-500 text-sm">مدعوم بالذكاء الاصطناعي - Gemini AI المجاني</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {AI_FEATURES.map(f => {
          const Icon = f.icon;
          return (
            <button key={f.id} onClick={() => { setActiveFeature(f.id); setResult(''); }}
              className={`p-3 rounded-xl border-2 text-center transition-all ${activeFeature === f.id ? 'border-primary-500 bg-primary-50 shadow-md' : 'border-gray-200 hover:border-primary-300'}`}>
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mx-auto mb-2`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <p className="text-xs font-bold text-gray-800">{f.label}</p>
              <p className="text-[10px] text-gray-400 mt-0.5">{f.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Chat Feature */}
      {activeFeature === 'chat' && (
        <Card>
          <CardContent className="p-0">
            <div className="h-[500px] flex flex-col">
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {chatHistory.length === 0 && (
                  <div className="text-center py-20">
                    <Sparkles className="w-12 h-12 text-primary-300 mx-auto mb-3" />
                    <p className="text-gray-400 font-medium">مرحباً! أنا المساعد الذكي</p>
                    <p className="text-gray-400 text-sm mt-1">اسألني أي سؤال عن الموظفين أو الحضور أو الرواتب</p>
                    <div className="flex flex-wrap justify-center gap-2 mt-4">
                      {['كم عدد الموظفين النشطين؟', 'من أكثر الموظفين غياباً؟', 'ما هو إجمالي الرواتب؟'].map(q => (
                        <button key={q} onClick={() => { setChatMessage(q); }}
                          className="text-xs bg-primary-50 text-primary-600 px-3 py-1.5 rounded-full hover:bg-primary-100">{q}</button>
                      ))}
                    </div>
                  </div>
                )}
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                      msg.role === 'user' ? 'bg-primary-600 text-white rounded-br-sm' : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                    }`}>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                      <span className="text-sm text-gray-500">جاري التفكير...</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="border-t p-3">
                <div className="flex gap-2">
                  <input value={chatMessage} onChange={e => setChatMessage(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleChat()}
                    placeholder="اكتب سؤالك هنا..." disabled={loading}
                    className="flex-1 h-11 px-4 rounded-xl border-2 border-gray-200 text-sm focus:border-primary-500 outline-none disabled:opacity-50" />
                  <Button onClick={handleChat} disabled={loading || !chatMessage.trim()} className="h-11 px-6">
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Features */}
      {activeFeature !== 'chat' && (
        <Card>
          <CardContent className="p-6 space-y-4">
            {activeFeature === 'report' && (
              <div>
                <label className="text-sm font-semibold text-gray-700 mb-2 block">نوع التقرير</label>
                <div className="flex gap-2 flex-wrap">
                  {[{ v: 'general', l: 'عام' }, { v: 'employees', l: 'الموظفين' }, { v: 'attendance', l: 'الحضور' }, { v: 'evaluations', l: 'التقييمات' }, { v: 'financial', l: 'المالي' }].map(o => (
                    <button key={o.v} onClick={() => setReportType(o.v)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium ${reportType === o.v ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>{o.l}</button>
                  ))}
                </div>
              </div>
            )}
            <Button onClick={() => handleAnalyze(activeFeature)} disabled={loading} className="w-full">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin ml-2" /> جاري التحليل...</> : <><Sparkles className="w-4 h-4 ml-2" /> بدء التحليل</>}
            </Button>
            {result && (
              <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-5 h-5 text-primary-500" />
                  <span className="font-bold text-gray-800">نتائج التحليل</span>
                </div>
                <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{result}</div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
