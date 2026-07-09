import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Leaf, Shield, Target, Heart, Eye, ChevronLeft, ChevronRight, Sparkles, Award, Users, Building2, CheckCircle, Globe, Star, Droplets, Zap, ArrowLeft } from 'lucide-react';

const policyItems = [
  {
    icon: Shield,
    title: 'سياسة الجودة',
    subtitle: 'معايير عالمية',
    description: 'نسعى لتقديم أعلى مستويات الجودة في خدمات النظافة والصيانة، مع الالتزام بالمعايير الدولية (ISO 9001) وأفضل الممارسات العالمية لضمان رضا العملاء وتحقيق التميز المستدام.',
    color: 'from-blue-500 to-blue-700',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    iconBg: 'bg-gradient-to-br from-blue-400 to-blue-600',
    features: ['ISO 9001', 'جودة عالية', 'تحسين مستمر'],
  },
  {
    icon: Target,
    title: 'رسالتنا',
    subtitle: 'ريادة השירות',
    description: 'أن نكون الشركة الرائدة في مجال خدمات النظافة والصيانة في اليمن، من خلال توفير خدمات متميزة تلبي احتياجات عملائنا بأعلى معايير الاحترافية والكفاءة.',
    color: 'from-emerald-500 to-emerald-700',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    iconBg: 'bg-gradient-to-br from-emerald-400 to-emerald-600',
    features: ['ريادة السوق', 'خدمة متميزة', 'احترافية عالية'],
  },
  {
    icon: Eye,
    title: 'رؤيتنا',
    subtitle: 'حلول مبتكرة',
    description: 'نسعى لتمكين الفرق من خلال حلول تقنية مبتكرة تحسّن كفاءة العمليات وتوفر رؤى قيّمة لاتخاذ القرارات، مع الابتكار المستمر في خدمات النظافة.',
    color: 'from-purple-500 to-purple-700',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
    iconBg: 'bg-gradient-to-br from-purple-400 to-purple-600',
    features: ['تقنية حديثة', 'كفاءة عالية', 'ابتكار مستمر'],
  },
  {
    icon: Heart,
    title: 'قيمنا',
    subtitle: 'أخلاق واحترام',
    description: 'النزاهية والشفافية في التعامل، والاحترام المتبادل، والعمل بروح الفريق، والسعي الدائم للتميز والابتكار مع الالتزام بأعلى معايير السلامة والصحة المهنية.',
    color: 'from-rose-500 to-rose-700',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/20',
    iconBg: 'bg-gradient-to-br from-rose-400 to-rose-600',
    features: ['نزاهة وشفافية', 'عمل فريق', 'سلامة مهنية'],
  },
];

const partners = [
  {
    name: 'الشركة اليمنية لتكرير السكر',
    nameEn: 'Yemen Company for Sugar Refining',
    logo: '/sugar-company.png',
    color: 'from-amber-400 to-orange-500',
    description: 'شريك استراتيجي في توفير الحلول الصناعية',
  },
  {
    name: 'شركة رأس عيسى الصناعية',
    nameEn: 'Ras Issa Industrial Company',
    logo: '/ras-issa-logo.webp',
    color: 'from-blue-400 to-indigo-500',
    description: 'شريك في قطاع الصناعة والتصنيع',
  },
  {
    name: 'الشركة اليمنية للمطاحن وصوامع الغلال',
    nameEn: 'Yemen Company for Flour Mills and Silos',
    logo: '/flour-mills-logo.webp',
    color: 'from-emerald-400 to-teal-500',
    description: 'شريك في قطاع الغلال والصوامع - الحديدة',
  },
];

const standards = [
  { icon: Droplets, text: 'خدمات التنظيف المتقدمة' },
  { icon: Sparkles, text: 'معايير النظافة العالمية' },
  { icon: Zap, text: 'تقنيات حديثة ومتطورة' },
  { icon: Globe, text: 'التزام بالمعايير الدولية' },
];

export default function SplashPage() {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<'policy' | 'partners'>('policy');

  useEffect(() => {
    setIsVisible(true);
    const interval = setInterval(() => {
      setCurrentSlide(prev => (prev + 1) % policyItems.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleContinue = () => {
    setIsVisible(false);
    setTimeout(() => navigate('/login'), 500);
  };

  const nextSlide = () => setCurrentSlide(prev => (prev + 1) % policyItems.length);
  const prevSlide = () => setCurrentSlide(prev => (prev - 1 + policyItems.length) % policyItems.length);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/3 left-1/4 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute bottom-1/3 right-1/4 w-72 h-72 bg-cyan-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '3s' }} />
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }} />
      </div>

      <div className={`relative z-10 min-h-screen flex flex-col transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
        
        {/* Header with Logo */}
        <header className="pt-8 pb-4 px-6">
          <div className="max-w-6xl mx-auto">
            {/* Logo Section */}
            <div className="flex flex-col items-center mb-6">
              {/* Logo Container */}
              <div className="relative mb-4">
                <img src="/logo.png" alt="أرض الجوهرة" className="w-32 h-32 object-contain drop-shadow-2xl" />
              </div>
              
              {/* Company Name */}
              <div className="text-center">
                <h1 className="text-4xl md:text-5xl font-black text-white mb-2 tracking-tight">
                  أرض الجوهرة
                </h1>
                <div className="flex items-center justify-center gap-3">
                  <div className="h-px w-12 bg-gradient-to-r from-transparent to-blue-400" />
                  <p className="text-blue-300 text-lg font-medium">لخدمات النظافة والصيانة</p>
                  <div className="h-px w-12 bg-gradient-to-l from-transparent to-blue-400" />
                </div>
              </div>
            </div>

            {/* Quality Standards Banner */}
            <div className="flex flex-wrap justify-center gap-3 mb-6">
              {standards.map((item, i) => {
                const Icon = item.icon;
                return (
                  <div key={i} className="flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-full border border-white/10">
                    <Icon className="w-4 h-4 text-blue-400" />
                    <span className="text-white/80 text-xs font-medium">{item.text}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 px-4 py-6 max-w-6xl mx-auto w-full">
          
          {/* Tab Navigation */}
          <div className="flex justify-center mb-6">
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-1.5 border border-white/10">
              <button
                onClick={() => setActiveTab('policy')}
                className={`px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
                  activeTab === 'policy'
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30'
                    : 'text-white/60 hover:text-white/80'
                }`}
              >
                سياساتنا وأهدافنا
              </button>
              <button
                onClick={() => setActiveTab('partners')}
                className={`px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
                  activeTab === 'partners'
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30'
                    : 'text-white/60 hover:text-white/80'
                }`}
              >
                شركاؤنا
              </button>
            </div>
          </div>

          {/* Policy Section */}
          {activeTab === 'policy' && (
            <div className="space-y-6">
              {/* Main Carousel */}
              <div className="relative">
                <div className="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 overflow-hidden shadow-2xl">
                  <div className="relative min-h-[280px] md:min-h-[240px]">
                    {policyItems.map((item, index) => {
                      const Icon = item.icon;
                      const isActive = index === currentSlide;
                      return (
                        <div
                          key={index}
                          className={`absolute inset-0 transition-all duration-700 ease-in-out ${
                            isActive ? 'opacity-100 translate-x-0 scale-100' : 'opacity-0 translate-x-8 scale-95 pointer-events-none'
                          }`}
                        >
                          <div className="h-full p-6 md:p-8">
                            <div className="flex flex-col md:flex-row items-center gap-6 h-full">
                              {/* Icon */}
                              <div className={`w-20 h-20 ${item.iconBg} rounded-2xl flex items-center justify-center flex-shrink-0 shadow-xl transform transition-transform duration-500 ${isActive ? 'scale-100 rotate-0' : 'scale-75 rotate-12'}`}>
                                <Icon className="w-10 h-10 text-white drop-shadow-lg" />
                              </div>
                              
                              {/* Content */}
                              <div className="flex-1 text-center md:text-right">
                                <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                                  <span className={`text-xs font-bold px-3 py-1 rounded-full bg-gradient-to-r ${item.color} text-white`}>
                                    {item.subtitle}
                                  </span>
                                </div>
                                <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">{item.title}</h2>
                                <p className="text-blue-100/90 text-base leading-relaxed mb-4">{item.description}</p>
                                
                                {/* Features */}
                                <div className="flex flex-wrap justify-center md:justify-start gap-2">
                                  {item.features.map((feature, fi) => (
                                    <span key={fi} className="flex items-center gap-1.5 text-xs text-white/70 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
                                      <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                                      {feature}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Navigation */}
                  <div className="flex items-center justify-between p-4 border-t border-white/10">
                    <button
                      onClick={prevSlide}
                      className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-all"
                    >
                      <ChevronRight className="w-5 h-5 text-white" />
                    </button>
                    
                    {/* Dots */}
                    <div className="flex gap-2">
                      {policyItems.map((_, index) => (
                        <button
                          key={index}
                          onClick={() => setCurrentSlide(index)}
                          className={`transition-all duration-300 rounded-full ${
                            index === currentSlide
                              ? 'w-8 h-2 bg-gradient-to-r from-blue-400 to-indigo-500'
                              : 'w-2 h-2 bg-white/30 hover:bg-white/50'
                          }`}
                        />
                      ))}
                    </div>
                    
                    <button
                      onClick={nextSlide}
                      className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-all"
                    >
                      <ChevronLeft className="w-5 h-5 text-white" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Goals Grid */}
              <div>
                <h3 className="text-center text-white/60 text-sm font-semibold mb-4 uppercase tracking-widest">أهدافنا الاستراتيجية</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { icon: Award, text: 'رضا 98% من العملاء', gradient: 'from-amber-400 to-orange-500' },
                    { icon: Users, text: 'بيئة عمل آمنة ومحفزة', gradient: 'from-blue-400 to-cyan-500' },
                    { icon: Building2, text: 'تغطية جميع المحافظات', gradient: 'from-purple-400 to-pink-500' },
                    { icon: Sparkles, text: 'أحدث تقنيات النظافة', gradient: 'from-emerald-400 to-teal-500' },
                  ].map((goal, index) => {
                    const Icon = goal.icon;
                    return (
                      <div
                        key={index}
                        className="group bg-white/5 backdrop-blur-sm rounded-2xl p-5 border border-white/10 text-center hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:border-white/20"
                      >
                        <div className={`w-12 h-12 bg-gradient-to-br ${goal.gradient} rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:scale-110 transition-transform`}>
                          <Icon className="w-6 h-6 text-white" />
                        </div>
                        <p className="text-white/90 text-sm font-medium">{goal.text}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Partners Section */}
          {activeTab === 'partners' && (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-2">شركاؤنا الاستراتيجيون</h3>
                <p className="text-blue-200/70">نفخر بالعمل مع أرقى الشركات في اليمن</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {partners.map((partner, index) => (
                  <div
                    key={index}
                    className="group relative bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 overflow-hidden hover:border-white/20 transition-all duration-500 hover:scale-105"
                  >
                    {/* Gradient Top */}
                    <div className={`h-2 bg-gradient-to-r ${partner.color}`} />
                    
                    <div className="p-6 text-center">
                      {/* Icon */}
                      <div className={`w-24 h-24 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl overflow-hidden bg-white`}>
                        {partner.logo ? (
                          <img src={partner.logo} alt={partner.name} className="w-full h-full object-contain p-1" />
                        ) : (
                          <div className={`w-full h-full bg-gradient-to-br ${partner.color} flex items-center justify-center text-4xl`}>
                            {partner.icon}
                          </div>
                        )}
                      </div>
                      
                      {/* Company Info */}
                      <h4 className="text-xl font-bold text-white mb-1">{partner.name}</h4>
                      <p className="text-blue-300/60 text-xs mb-3">{partner.nameEn}</p>
                      <div className="h-px w-16 bg-gradient-to-r from-transparent via-white/20 to-transparent mx-auto mb-3" />
                      <p className="text-white/60 text-sm">{partner.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Partnership Message */}
              <div className="bg-gradient-to-r from-blue-500/10 to-indigo-500/10 rounded-2xl p-6 border border-blue-500/20 text-center">
                <Star className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
                <p className="text-white/80 text-lg font-medium">
                  نلتزم بتقديم أفضل خدمات النظافة والصيانة لشركائنا الكرام
                </p>
                <p className="text-white/50 text-sm mt-2">
                  جودة عالية • أسعار منافسة • التزام بالمواعيد
                </p>
              </div>
            </div>
          )}

          {/* Continue Button */}
          <div className="flex justify-center mt-8 mb-4">
            <button
              onClick={handleContinue}
              className="group bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-4 px-14 rounded-2xl transition-all duration-300 shadow-xl shadow-blue-500/30 hover:shadow-2xl hover:shadow-blue-500/40 hover:scale-105 flex items-center gap-3"
            >
              <span className="text-lg">تسجيل الدخول</span>
              <ArrowLeft className="w-6 h-6 transition-transform group-hover:-translate-x-1" />
            </button>
          </div>
        </main>

        {/* Footer */}
        <footer className="pb-6 px-4">
          <div className="max-w-6xl mx-auto">
            {/* Designer Credit */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-white/10 mb-4">
              <div className="flex flex-col md:flex-row items-center justify-center gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl overflow-hidden bg-white shadow-lg">
                    <img src="/alghith-logo.png" alt="الغيث" className="w-full h-full object-contain" />
                  </div>
                  <div className="text-center md:text-right">
                    <p className="text-white/90 text-sm font-semibold">تصميم وتطوير</p>
                    <a 
                      href="https://alghithapp.netlify.app/" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-sm font-bold transition-colors"
                    >
                      الغيث لتصميم التطبيقات والأنظمة
                    </a>
                  </div>
                </div>
                <div className="h-8 w-px bg-white/20 hidden md:block" />
                <div className="text-center">
                  <p className="text-white/50 text-xs">
                    © 2026 أرض الجوهرة لخدمات النظافة. جميع الحقوق محفوظة.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
