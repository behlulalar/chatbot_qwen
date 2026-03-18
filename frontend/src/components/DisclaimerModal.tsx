import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import './DisclaimerModal.css';

interface DisclaimerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function DisclaimerModal({ isOpen, onClose }: DisclaimerModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="disclaimer-modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="disclaimer-modal" onClick={(e) => e.stopPropagation()}>
        <div className="disclaimer-modal-header">
          <h3>Yasal Uyarı ve Sorumluluk Reddi Beyanı</h3>
          <button className="disclaimer-modal-close" onClick={onClose} aria-label="Kapat">
            <X size={20} />
          </button>
        </div>

        <div className="disclaimer-modal-body">
          <p>
            İşbu uygulama, yapay zekâ teknolojisiyle desteklenen bir bilgi asistanıdır. Sistem tarafından sunulan yanıtlar,
            mevcut mevzuat ve bilgi kaynaklarından otomatik olarak derlenmekte olup; sistemsel hatalar, eksiklikler veya
            güncelliğini yitirmiş bilgiler içerme ihtimali barındırmaktadır.
          </p>

          <h4>Kullanım Koşulları ve Yükümlülükler</h4>
          <ul>
            <li>
              Sistem tarafından üretilen içerikler bilgilendirme amaçlıdır; hiçbir surette hukuki mütalaa, bağlayıcı
              tavsiye, tebligat veya kesin karar niteliği taşımamaktadır.
            </li>
            <li>
              Resmî işlem ve süreçlerde yahut karar gerektiren idari durumlarda, yalnızca ilgili birimlerce yayımlanan
              resmî mevzuat hükümleri, güncel duyurular ve yetkili mercilerin/uzmanların görüşleri esas alınmalıdır.
            </li>
            <li>
              Sistem çıktılarının doğruluğunu, güncelliğini ve geçerli mevzuata uygunluğunu ilgili asıl kaynaklardan teyit
              etme yükümlülüğü münhasıran kullanıcıya aittir.
            </li>
          </ul>

          <h4>Hukuki Sorumluluk Reddi</h4>
          <p>
            İşbu yapay zekâ asistanının ürettiği yanıtların veya sağladığı bilgilerin kullanımından doğabilecek doğrudan,
            dolaylı, maddi veya manevi zararlardan, hak kayıplarından yahut hukuki ihtilaflardan Sakarya Uygulamalı Bilimler
            Üniversitesi Bilgi İşlem Daire Başkanlığı (<strong>SUBÜ BİDB</strong>) ve ilgili paydaşlar hiçbir şekilde
            sorumlu tutulamaz.
          </p>

          <h4>Geri Bildirim</h4>
          <p>
            Sistemin optimizasyonuna ve gelişimine katkı sağlamak amacıyla, hatalı veya eksik olduğunu değerlendirdiğiniz
            içerikleri lütfen geri bildirim araçları vasıtasıyla ilgili birimimize iletiniz.
          </p>
        </div>
      </div>
    </div>
  );
}

