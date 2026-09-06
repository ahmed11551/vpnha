import React from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { X, Copy, Check, ExternalLink, ShieldCheck } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface QrModalProps {
  isOpen: boolean;
  onClose: () => void;
  vlessLink: string;
  serverName?: string;
  onCopy: () => void;
  hasCopied: boolean;
}

export const QrModal: React.FC<QrModalProps> = ({
  isOpen,
  onClose,
  vlessLink,
  serverName = 'NexusVPN Frankfurt',
  onCopy,
  hasCopied,
}) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-md"
          />

          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 350 }}
            className="relative w-full max-w-sm rounded-3xl bg-[#0e1320] border border-white/10 p-6 shadow-2xl text-center overflow-hidden"
          >
            {/* Ambient background glow */}
            <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-48 h-48 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

            <button
              id="qr-close-btn"
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-full bg-white/5 hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center justify-center space-x-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>VLESS + Reality QR Code</span>
            </div>

            <h3 className="text-lg font-bold text-white mb-1">Отсканируйте камерой</h3>
            <p className="text-xs text-slate-400 mb-5">
              Подходит для приложений Happ, AmneziaVPN, Streisand, v2rayNG или v2rayN
            </p>

            {/* QR code canvas card */}
            <div className="inline-flex p-4 rounded-2xl bg-white shadow-xl shadow-cyan-950/40 mb-5">
              <QRCodeSVG
                value={vlessLink || 'vless://nexusvpn-preview'}
                size={210}
                level="M"
                includeMargin={false}
              />
            </div>

            <div className="space-y-2">
              <button
                id="modal-copy-key-btn"
                onClick={onCopy}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-black font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/50 transition-all active:scale-98"
              >
                {hasCopied ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Скопировано в буфер!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Скопировать ключ VLESS</span>
                  </>
                )}
              </button>

              <p className="text-[11px] text-slate-400 pt-1">
                Сервер: <span className="text-slate-200">{serverName}</span>
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
