import { useState, useEffect, useRef } from 'react';
import { Printer, Upload, User, Search, Download, CreditCard } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import api from '@/api/client';

export default function EmployeeCardsPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [photos, setPhotos] = useState<Record<number, string>>({});
  const [selectedEmployees, setSelectedEmployees] = useState<Set<number>>(new Set());
  const printRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get('/employees').then(res => {
      const list = (res.data.data || []).filter((e: any) => e.is_active);
      setEmployees(list);
      const saved: Record<number, string> = {};
      list.forEach((e: any) => {
        const p = localStorage.getItem(`card_photo_${e.id}`);
        if (p) saved[e.id] = p;
      });
      setPhotos(saved);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handlePhotoUpload = (empId: number, file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setPhotos(prev => ({ ...prev, [empId]: base64 }));
      localStorage.setItem(`card_photo_${empId}`, base64);
    };
    reader.readAsDataURL(file);
  };

  const toggleSelect = (id: number) => {
    setSelectedEmployees(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    const filtered = employees.filter(e => e.name?.includes(search));
    setSelectedEmployees(new Set(filtered.map(e => e.id)));
  };

  const deselectAll = () => setSelectedEmployees(new Set());

  const filtered = employees.filter(e => e.name?.includes(search));
  const toPrint = employees.filter(e => selectedEmployees.has(e.id));

  const handlePrint = () => {
    const win = window.open('', '_blank');
    if (!win) return;
    const cards = toPrint.map(emp => {
      const photo = photos[emp.id] || '';
      return `
        <div class="card">
          <div class="card-header">
            <div class="company-logo">🌍</div>
            <div class="company-name">ارض الجوهرة لخدمات النظافة</div>
            <div class="company-sub">EARTH AL-JAWHARA FOR CLEANING SERVICES</div>
          </div>
          <div class="card-body">
            <div class="photo-section">
              ${photo ? `<img src="${photo}" class="photo" />` : `<div class="photo-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/></svg></div>`}
            </div>
            <div class="info-section">
              <div class="emp-name">${emp.name || emp.full_name || '—'}</div>
              <div class="emp-code">الكود: ${emp.code || emp.employee_code || '—'}</div>
              <div class="emp-detail"><span class="label">الوظيفة:</span> ${emp.position || emp.job_title || '—'}</div>
              <div class="emp-detail"><span class="label">الشركة:</span> ${emp.company_name || '—'}</div>
              <div class="emp-detail"><span class="label">الهاتف:</span> ${emp.phone || '—'}</div>
              ${emp.region ? `<div class="emp-detail"><span class="label">المنطقة:</span> ${emp.region}</div>` : ''}
            </div>
          </div>
          <div class="card-footer">
            <div class="qr-placeholder">EARTH AL-JAWHARA</div>
          </div>
        </div>`;
    }).join('');

    win.document.write(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>بطاقات عمل الموظفين</title>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Cairo', Arial, sans-serif; background: #f3f4f6; direction: rtl; }
        @media print { body { background: white; } .no-print { display: none !important; } .card { break-inside: avoid; page-break-inside: avoid; } }
        .toolbar { position: fixed; top: 0; left: 0; right: 0; z-index: 9999; background: #1f2937; padding: 10px 20px; display: flex; align-items: center; gap: 10px; direction: rtl; }
        .toolbar button { padding: 8px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-family: 'Cairo', sans-serif; color: white; font-weight: 600; }
        .btn-print { background: #059669; } .btn-close { background: #dc2626; }
        .toolbar span { color: white; font-size: 13px; margin-right: auto; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 60px 20px 20px; max-width: 1200px; margin: 0 auto; }
        @media print { .grid { padding: 10px; gap: 15px; } }
        .card { width: 100%; border: 2px solid #059669; border-radius: 16px; overflow: hidden; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .card-header { background: linear-gradient(135deg, #059669, #10b981); padding: 16px; text-align: center; color: white; }
        .company-logo { font-size: 32px; margin-bottom: 4px; }
        .company-name { font-size: 14px; font-weight: 700; }
        .company-sub { font-size: 9px; opacity: 0.8; margin-top: 2px; letter-spacing: 1px; }
        .card-body { padding: 20px; display: flex; gap: 16px; align-items: flex-start; }
        .photo-section { flex-shrink: 0; }
        .photo { width: 90px; height: 90px; border-radius: 12px; object-fit: cover; border: 3px solid #059669; }
        .photo-placeholder { width: 90px; height: 90px; border-radius: 12px; border: 2px dashed #d1d5db; display: flex; align-items: center; justify-content: center; color: #9ca3af; background: #f9fafb; }
        .info-section { flex: 1; min-width: 0; }
        .emp-name { font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .emp-code { font-size: 11px; color: #6b7280; margin-bottom: 8px; background: #f3f4f6; padding: 2px 8px; border-radius: 4px; display: inline-block; }
        .emp-detail { font-size: 12px; color: #374151; margin-bottom: 3px; }
        .emp-detail .label { font-weight: 600; color: #059669; }
        .card-footer { border-top: 1px solid #e5e7eb; padding: 8px 16px; text-align: center; }
        .qr-placeholder { font-size: 8px; color: #9ca3af; letter-spacing: 2px; }
      </style></head><body>
      <div class="toolbar no-print">
        <button class="btn-print" onclick="window.print()">🖨️ طباعة البطاقات</button>
        <button class="btn-close" onclick="window.close()">✖ إغلاق</button>
        <span>${toPrint.length} بطاقة عمل — ارض الجوهرة لخدمات النظافة</span>
      </div>
      <div class="grid">${cards}</div>
    </body></html>`);
    win.document.close();
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">بطاقات عمل الموظفين</h1>
          <p className="text-gray-500 text-sm mt-1">تصميم وطباعة بطاقات عمل حديثة وأنيقة</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={selectAll}>تحديد الكل</Button>
          <Button variant="outline" onClick={deselectAll}>إلغاء التحديد</Button>
          <Button onClick={handlePrint} disabled={selectedEmployees.size === 0}>
            <Printer className="w-4 h-4" /> طباعة ({selectedEmployees.size})
          </Button>
        </div>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="بحث بالاسم..." className="w-full h-10 pr-10 pl-4 rounded-lg border-2 border-gray-200 text-sm focus:border-primary-500 outline-none" />
          </div>
        </CardContent>
      </Card>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((emp) => {
          const isSelected = selectedEmployees.has(emp.id);
          const photo = photos[emp.id];
          return (
            <div key={emp.id} onClick={() => toggleSelect(emp.id)}
              className={`cursor-pointer rounded-2xl border-2 overflow-hidden transition-all hover:shadow-lg ${isSelected ? 'border-primary-500 ring-2 ring-primary-200' : 'border-gray-200 hover:border-primary-300'}`}>
              {/* Card Header */}
              <div className="bg-gradient-to-br from-primary-600 to-primary-500 p-4 text-center text-white">
                <div className="text-3xl mb-1">🌍</div>
                <div className="font-bold text-sm">ارض الجوهرة لخدمات النظافة</div>
                <div className="text-[9px] opacity-80 tracking-wider">EARTH AL-JAWHARA FOR CLEANING SERVICES</div>
              </div>
              {/* Card Body */}
              <div className="bg-white p-4 flex gap-3 items-start">
                <div className="flex-shrink-0 relative group">
                  {photo ? (
                    <img src={photo} alt={emp.name} className="w-20 h-20 rounded-xl object-cover border-3 border-primary-500" />
                  ) : (
                    <div className="w-20 h-20 rounded-xl border-2 border-dashed border-gray-300 flex items-center justify-center bg-gray-50 text-gray-400">
                      <User className="w-8 h-8" />
                    </div>
                  )}
                  <label className="absolute inset-0 flex items-center justify-center bg-black/40 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
                    <Upload className="w-5 h-5 text-white" />
                    <input type="file" accept="image/*" className="hidden" onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handlePhotoUpload(emp.id, file);
                    }} />
                  </label>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-gray-900 text-sm truncate">{emp.name || emp.full_name}</div>
                  <div className="text-[10px] text-gray-500 bg-gray-100 px-2 py-0.5 rounded inline-block mt-1">الكود: {emp.code || emp.employee_code || '—'}</div>
                  <div className="text-xs text-gray-600 mt-1.5"><span className="font-semibold text-primary-600">الوظيفة:</span> {emp.position || emp.job_title || '—'}</div>
                  <div className="text-xs text-gray-600"><span className="font-semibold text-primary-600">الشركة:</span> {emp.company_name || '—'}</div>
                  <div className="text-xs text-gray-500"><span className="font-semibold text-primary-600">الهاتف:</span> {emp.phone || '—'}</div>
                  {emp.region && <div className="text-xs text-gray-500"><span className="font-semibold text-primary-600">المنطقة:</span> {emp.region}</div>}
                </div>
              </div>
              {/* Card Footer */}
              <div className="border-t border-gray-100 px-4 py-2 text-center">
                <span className="text-[8px] text-gray-400 tracking-widest">EARTH AL-JAWHARA</span>
              </div>
              {/* Selection Indicator */}
              {isSelected && (
                <div className="bg-primary-50 border-t border-primary-100 px-4 py-1.5 text-center">
                  <span className="text-xs font-medium text-primary-600">✓ محدد للطباعة</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <CreditCard className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>لا توجد نتائج</p>
        </div>
      )}
    </div>
  );
}
