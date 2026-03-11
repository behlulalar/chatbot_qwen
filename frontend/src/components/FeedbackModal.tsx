import React, { useState } from 'react';
import { X } from 'lucide-react';
import './FeedbackModal.css';

export const NEGATIVE_REASONS = [
  { id: 'mevzuata_uygun_degil', label: 'Mevzuata uygun değil' },
  { id: 'cumle_yarim_kalmis', label: 'Cümle yarım kalmış' },
  { id: 'soruya_cevap_vermedi', label: 'Soruma cevap vermedi' },
  { id: 'kaynak_yetersiz', label: 'Kaynak yetersiz veya hatalı' },
  { id: 'yanlis_bilgi', label: 'Yanlış veya eksik bilgi' },
  { id: 'okunakli_degil', label: 'Okunaklı / anlaşılır değil' },
  { id: 'diger', label: 'Diğer' },
] as const;

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (rating: 'positive' | 'negative', reason?: string, comment?: string) => void;
  isNegative?: boolean;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isNegative = true,
}) => {
  const [selectedReason, setSelectedReason] = useState<string | null>(null);
  const [comment, setComment] = useState('');

  const handleSubmit = () => {
    if (isNegative && !selectedReason) return;
    onSubmit(
      isNegative ? 'negative' : 'positive',
      isNegative ? selectedReason || undefined : undefined,
      comment.trim() || undefined
    );
    setSelectedReason(null);
    setComment('');
    onClose();
  };

  const handleClose = () => {
    setSelectedReason(null);
    setComment('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="feedback-modal-overlay" onClick={handleClose}>
      <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
        <div className="feedback-modal-header">
          <h3>Geri bildirim paylaş</h3>
          <button className="feedback-modal-close" onClick={handleClose} aria-label="Kapat">
            <X size={20} />
          </button>
        </div>

        {isNegative ? (
          <>
            <p className="feedback-modal-hint">Neden yetersiz buldunuz? (en az birini seçin)</p>
            <div className="feedback-reasons">
              {NEGATIVE_REASONS.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  className={`feedback-reason-btn ${selectedReason === r.id ? 'selected' : ''}`}
                  onClick={() => setSelectedReason(selectedReason === r.id ? '' : r.id)}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </>
        ) : (
          <p className="feedback-modal-hint">İsteğe bağlı açıklama ekleyebilirsiniz.</p>
        )}

        <div className="feedback-modal-comment">
          <label htmlFor="feedback-comment">Detay (isteğe bağlı)</label>
          <textarea
            id="feedback-comment"
            placeholder="Ek açıklama yazabilirsiniz..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
          />
        </div>

        <div className="feedback-modal-actions">
          <button type="button" className="feedback-btn-cancel" onClick={handleClose}>
            İptal
          </button>
          <button
            type="button"
            className="feedback-btn-submit"
            onClick={handleSubmit}
            disabled={isNegative && !selectedReason}
          >
            Gönder
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackModal;
