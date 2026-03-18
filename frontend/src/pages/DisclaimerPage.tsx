import React from 'react';
import { Link } from 'react-router-dom';
import './DisclaimerPage.css';

export default function DisclaimerPage() {
  return (
    <div className="disclaimer-page">
      <div className="disclaimer-card">
        <div className="disclaimer-header">
          <h1>Yasal Uyarı ve Sorumluluk Reddi Beyanı</h1>
          <Link className="disclaimer-back" to="/">
            ← Sohbete dön
          </Link>
        </div>

        <p>
          İşbu uygulama, yapay zekâ teknolojisiyle desteklenen bir bilgi asistanıdır. Sistem tarafından sunulan yanıtlar,
          mevcut mevzuat ve bilgi kaynaklarından otomatik olarak derlenmekte olup; sistemsel hatalar, eksiklikler veya
          güncelliğini yitirmiş bilgiler içerme ihtimali barındırmaktadır.
        </p>

        <h2>Kullanım Koşulları ve Yükümlülükler</h2>
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

        <h2>Hukuki Sorumluluk Reddi</h2>
        <p>
          İşbu yapay zekâ asistanının ürettiği yanıtların veya sağladığı bilgilerin kullanımından doğabilecek doğrudan,
          dolaylı, maddi veya manevi zararlardan, hak kayıplarından yahut hukuki ihtilaflardan Sakarya Uygulamalı Bilimler
          Üniversitesi Bilgi İşlem Daire Başkanlığı (<strong>SUBÜ BİDB</strong>) ve ilgili paydaşlar hiçbir şekilde sorumlu
          tutulamaz.
        </p>

        <h2>Geri bildirim</h2>
        <p>
          Sistemin optimizasyonuna ve gelişimine katkı sağlamak amacıyla, hatalı veya eksik olduğunu değerlendirdiğiniz
          içerikleri lütfen geri bildirim araçları vasıtasıyla ilgili birimimize iletiniz.
        </p>
      </div>
    </div>
  );
}

