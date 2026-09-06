import React, { useState } from 'react';
import { Copy, Check, Download, FileCode, Terminal, Layers, Database, Layout, ShieldCheck } from 'lucide-react';
import { CODE_FILES } from '../data/codeFiles';
import { CodeFile } from '../types';

interface CodeExplorerProps {
  initialFile?: string;
}

export const CodeExplorer: React.FC<CodeExplorerProps> = ({ initialFile }) => {
  const [selectedFile, setSelectedFile] = useState<CodeFile>(
    CODE_FILES.find(f => f.filename === initialFile) || CODE_FILES[0]
  );
  const [copied, setCopied] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const handleCopy = () => {
    navigator.clipboard.writeText(selectedFile.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([selectedFile.code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = selectedFile.filename.split('/').pop() || 'file.txt';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const filteredFiles = selectedCategory === 'all'
    ? CODE_FILES
    : CODE_FILES.filter(f => f.category === selectedCategory);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'core': return <Terminal className="w-3.5 h-3.5 text-emerald-400" />;
      case 'bot': return <Terminal className="w-3.5 h-3.5 text-cyan-400" />;
      case 'database': return <Database className="w-3.5 h-3.5 text-indigo-400" />;
      case 'frontend': return <Layout className="w-3.5 h-3.5 text-amber-400" />;
      default: return <FileCode className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col h-[760px]">
      
      {/* Top Bar with Category Filter */}
      <div className="bg-slate-950 px-5 py-3.5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
          <span className="text-xs font-mono text-slate-400 ml-2 font-semibold">NexusVPN Architecture Source Code</span>
        </div>

        {/* Category Pills */}
        <div className="flex space-x-1.5 overflow-x-auto text-xs">
          {[
            { id: 'all', label: 'Все файлы' },
            { id: 'core', label: 'API & Marzban' },
            { id: 'bot', label: 'aiogram 3 Bot' },
            { id: 'database', label: 'БД & Модели' },
            { id: 'frontend', label: 'Mini App' },
            { id: 'deployment', label: 'Деплой' },
          ].map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1 rounded-xl font-medium transition-all ${selectedCategory === cat.id ? 'bg-emerald-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        
        {/* Left Sidebar: File List */}
        <div className="w-full md:w-64 bg-slate-950/60 border-r border-slate-800 p-3 overflow-y-auto space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-2 py-1">Файлы проекта:</div>
          {filteredFiles.map(file => {
            const isSelected = selectedFile.filename === file.filename;
            return (
              <button
                key={file.filename}
                onClick={() => setSelectedFile(file)}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-xs flex items-center justify-between transition-all ${isSelected ? 'bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 font-semibold' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'}`}
              >
                <div className="flex items-center space-x-2 truncate">
                  {getCategoryIcon(file.category)}
                  <span className="font-mono truncate">{file.filename}</span>
                </div>
                <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  {file.language}
                </span>
              </button>
            );
          })}
        </div>

        {/* Right Code Display Area */}
        <div className="flex-1 flex flex-col bg-slate-900/90 overflow-hidden">
          
          {/* File Header Details */}
          <div className="bg-slate-950/80 px-5 py-3 border-b border-slate-800 flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-sm font-bold text-white">{selectedFile.filename}</span>
                <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800/60 px-2 py-0.5 rounded-full font-mono">
                  {selectedFile.language}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">{selectedFile.description}</p>
            </div>

            {/* Action buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopy}
                className="bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded-xl text-xs font-medium flex items-center space-x-1.5 border border-slate-700 transition-all active:scale-95"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-300" />}
                <span>{copied ? 'Скопировано!' : 'Копировать'}</span>
              </button>

              <button
                onClick={handleDownload}
                className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1.5 rounded-xl text-xs font-bold flex items-center space-x-1.5 shadow-md transition-all active:scale-95"
                title="Скачать файл"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Скачать</span>
              </button>
            </div>
          </div>

          {/* Code Viewer with Line Numbers */}
          <div className="flex-1 overflow-auto p-4 font-mono text-xs text-slate-200 bg-[#07090e]">
            <pre className="leading-relaxed">
              <code>{selectedFile.code}</code>
            </pre>
          </div>

          {/* Footer Status Bar */}
          <div className="bg-slate-950 px-4 py-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
            <div className="flex items-center space-x-2 font-mono">
              <span>UTF-8</span>
              <span>•</span>
              <span>Python 3.10+ / Linux</span>
              <span>•</span>
              <span className="text-emerald-400 font-semibold">Ready for production</span>
            </div>
            <div className="flex items-center space-x-1 text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Marzban Xray VLESS + Reality Compatible</span>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
