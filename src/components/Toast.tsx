import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { CheckCircle2, AlertCircle, Info } from 'lucide-react';

interface ToastProps {
  message: string | null;
  type?: 'success' | 'error' | 'info';
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ message, type = 'success', onClose }) => {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          onClick={onClose}
          className="fixed top-4 left-4 right-4 z-50 max-w-sm mx-auto cursor-pointer"
        >
          <div
            className={`flex items-center space-x-2.5 px-4 py-3 rounded-2xl backdrop-blur-xl border shadow-2xl text-xs font-medium ${
              type === 'success'
                ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200 shadow-emerald-950/50'
                : type === 'error'
                ? 'bg-rose-950/90 border-rose-500/40 text-rose-200 shadow-rose-950/50'
                : 'bg-slate-900/90 border-cyan-500/40 text-cyan-200 shadow-cyan-950/50'
            }`}
          >
            {type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
            {type === 'error' && <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />}
            {type === 'info' && <Info className="w-4 h-4 text-cyan-400 shrink-0" />}
            <span className="flex-1">{message}</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
