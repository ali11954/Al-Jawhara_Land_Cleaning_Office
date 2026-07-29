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
    const logoUrl = window.location.origin + '/logo.svg';
    const cards = toPrint.map(emp => {
      const photo = photos[emp.id] || '';
      return `
        <div class="card">
          <div class="card-front">
            <div class="card-top">
              <img src="${logoUrl}" class="logo" />
              <div class="top-text">
                <div class="co-name-ar">أرض الجوهرة لخدمات النظافة</div>
                <div class="co-name-en">EARTH AL-JAWHARA FOR CLEANING SERVICES</div>
              </div>
            </div>
            <div class="card-body">
              <div class="photo-box">
                ${photo ? `<img src="${photo}" class="photo" />` : `<div class="photo-empty"><svg viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5" width="28" height="28"><path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/></svg></div>`}
              </div>
              <div class="details">
                <div class="emp-name">${emp.name || emp.full_name || '—'}</div>
                <div class="emp-code">${emp.code || emp.employee_code || '—'}</div>
                <div class="emp-row"><span class="lbl">الوظيفة:</span> ${emp.position || emp.job_title || '—'}</div>
                <div class="emp-row"><span class="lbl">الشركة:</span> ${emp.company_name || '—'}</div>
                <div class="emp-row"><span class="lbl">الهاتف:</span> ${emp.phone || '—'}</div>
              </div>
            </div>
            <div class="card-bottom">
              <div class="bottom-line"></div>
              <div class="bottom-info">
                <span>العنوان: صنعاء - الجمهورية اليمنية</span>
                <span>|</span>
                <span>هاتف: 777 123 456</span>
                <span>|</span>
                <span>info@al-jawhara.com</span>
              </div>
              <div class="card-notes">ملاحظات: هذه البطاقة ملك للشركة ويجب إعادتها عند الانتهاء من العمل. في حالة الفقدان يتم خصم 5000 ريال من الراتب.</div>
            </div>
          </div>
        </div>`;
    }).join('');

    win.document.write(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>بطاقات عمل الموظفين</title>
      <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Cairo', Arial, sans-serif; background: #e5e7eb; direction: rtl; }
        @media print {
          body { background: white; }
          .no-print { display: none !important; }
          .card { break-inside: avoid; page-break-inside: avoid; margin: 4mm auto; }
          .page-note { display: none; }
        }
        .toolbar { position: fixed; top: 0; left: 0; right: 0; z-index: 9999; background: #1f2937; padding: 10px 20px; display: flex; align-items: center; gap: 10px; direction: rtl; }
        .toolbar button { padding: 8px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-family: 'Cairo', sans-serif; color: white; font-weight: 600; }
        .btn-print { background: #059669; } .btn-close { background: #dc2626; }
        .toolbar span { color: white; font-size: 13px; margin-right: auto; }

        .page-note { text-align: center; padding: 10px; color: #6b7280; font-size: 11px; margin-top: 55px; }

        .cards-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 6mm; padding: 10mm; }

        /* Card: 90mm x 50mm */
        .card {
          width: 90mm;
          height: 50mm;
          border: 1.2mm solid #059669;
          border-radius: 3mm;
          overflow: hidden;
          background: white;
          box-shadow: 0 1mm 3mm rgba(0,0,0,0.12);
          position: relative;
        }

        .card-front {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        /* Top bar with logo */
        .card-top {
          background: linear-gradient(135deg, #059669 0%, #10b981 100%);
          padding: 2mm 3mm;
          display: flex;
          align-items: center;
          gap: 2mm;
          min-height: 10mm;
        }
        .logo {
          width: 8mm;
          height: 8mm;
          border-radius: 50%;
          border: 0.5mm solid rgba(255,255,255,0.5);
          object-fit: contain;
          background: white;
          flex-shrink: 0;
        }
        .top-text { flex: 1; min-width: 0; }
        .co-name-ar {
          font-size: 7pt;
          font-weight: 800;
          color: white;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          line-height: 1.3;
        }
        .co-name-en {
          font-size: 4.5pt;
          color: rgba(255,255,255,0.8);
          letter-spacing: 0.3px;
          line-height: 1.2;
        }

        /* Body */
        .card-body {
          flex: 1;
          display: flex;
          gap: 2.5mm;
          padding: 2mm 3mm;
          align-items: flex-start;
          min-height: 0;
        }

        .photo-box {
          flex-shrink: 0;
          width: 16mm;
          height: 20mm;
        }
        .photo {
          width: 16mm;
          height: 20mm;
          border-radius: 2mm;
          object-fit: cover;
          border: 0.5mm solid #059669;
        }
        .photo-empty {
          width: 16mm;
          height: 20mm;
          border-radius: 2mm;
          border: 0.4mm dashed #d1d5db;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f9fafb;
        }

        .details { flex: 1; min-width: 0; overflow: hidden; }
        .emp-name {
          font-size: 7pt;
          font-weight: 800;
          color: #111827;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          line-height: 1.4;
        }
        .emp-code {
          font-size: 5pt;
          color: #6b7280;
          background: #f3f4f6;
          padding: 0.3mm 1.5mm;
          border-radius: 1mm;
          display: inline-block;
          margin-bottom: 1mm;
        }
        .emp-row {
          font-size: 5pt;
          color: #374151;
          line-height: 1.5;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .emp-row .lbl {
          font-weight: 700;
          color: #059669;
        }

        /* Bottom */
        .card-bottom {
          border-top: 0.3mm solid #e5e7eb;
          padding: 1.2mm 3mm;
          background: #f9fafb;
        }
        .bottom-line {
          width: 100%;
          height: 0.4mm;
          background: linear-gradient(90deg, #059669, #10b981, #059669);
          border-radius: 1mm;
          margin-bottom: 1mm;
        }
        .bottom-info {
          font-size: 3.8pt;
          color: #6b7280;
          text-align: center;
          display: flex;
          justify-content: center;
          gap: 1.5mm;
          line-height: 1.4;
        }
        .card-notes {
          font-size: 3pt;
          color: #9ca3af;
          text-align: center;
          margin-top: 0.5mm;
          line-height: 1.3;
        }
      </style></head><body>
      <div class="toolbar no-print">
        <button class="btn-print" onclick="window.print()">🖨️ طباعة البطاقات</button>
        <button class="btn-close" onclick="window.close()">✖ إغلاق</button>
        <span>${toPrint.length} بطاقة عمل — مقاس 90×50 مم</span>
      </div>
      <div class="page-note">💡 مقاس البطاقة: 90 × 50 مم (مقاس البطاقة الشخصية القياسي)</div>
      <div class="cards-container">${cards}</div>
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
