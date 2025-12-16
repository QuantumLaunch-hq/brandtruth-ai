'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Download, 
  Package,
  FileImage,
  Check,
  Loader2,
  AlertCircle,
  ExternalLink,
  Archive,
  Monitor,
  Smartphone,
  Square,
  Image as ImageIcon
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FormatSpec {
  id: string;
  name: string;
  width: number;
  height: number;
  aspect_ratio: string;
  platforms: string[];
}

interface ExportedFile {
  format: string;
  name: string;
  dimensions: string;
  platforms: string[];
  file_path: string;
  size_kb: number;
}

interface ExportResult {
  success: boolean;
  headline: string;
  formats_exported: number;
  total_size_kb: number;
  export_time_ms: number;
  files: ExportedFile[];
  zip_path: string | null;
  errors: string[];
}

export default function ExportPage() {
  // Form state
  const [imageUrl, setImageUrl] = useState('https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=1200');
  const [headline, setHeadline] = useState('Stop Getting Rejected by ATS');
  const [cta, setCta] = useState('Get Started');
  const [brandName, setBrandName] = useState('Careerfied');
  
  // Format selection
  const [availableFormats, setAvailableFormats] = useState<FormatSpec[]>([]);
  const [selectedFormats, setSelectedFormats] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(true);
  
  // Result state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load available formats
  useEffect(() => {
    async function loadFormats() {
      try {
        const response = await fetch(`${API_BASE}/export/formats`);
        const data = await response.json();
        setAvailableFormats(data.formats);
        // Select all by default
        setSelectedFormats(new Set(data.formats.map((f: FormatSpec) => f.id)));
      } catch (err) {
        console.error('Failed to load formats:', err);
      }
    }
    loadFormats();
  }, []);

  const toggleFormat = (formatId: string) => {
    const newSelected = new Set(selectedFormats);
    if (newSelected.has(formatId)) {
      newSelected.delete(formatId);
    } else {
      newSelected.add(formatId);
    }
    setSelectedFormats(newSelected);
    setSelectAll(newSelected.size === availableFormats.length);
  };

  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedFormats(new Set());
    } else {
      setSelectedFormats(new Set(availableFormats.map(f => f.id)));
    }
    setSelectAll(!selectAll);
  };

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/export/all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_url: imageUrl,
          headline,
          cta,
          brand_name: brandName,
          formats: selectedFormats.size === availableFormats.length 
            ? null  // null = all formats
            : Array.from(selectedFormats),
          create_zip: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/export/demo`, {
        method: 'POST',
      });

      const data = await response.json();
      // Convert demo response to full result format
      setResult({
        success: data.success,
        headline: "Stop Getting Rejected by ATS",
        formats_exported: data.formats_exported,
        total_size_kb: data.total_size_kb,
        export_time_ms: data.export_time_ms,
        files: data.formats.map((f: any) => ({
          format: f.format,
          name: f.name,
          dimensions: f.dimensions,
          platforms: [],
          file_path: `/output/ad_demo_${f.format}.png`,
          size_kb: Math.floor(data.total_size_kb / data.formats_exported),
        })),
        zip_path: data.zip_path,
        errors: [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getFormatIcon = (formatId: string) => {
    if (['story', 'pin'].includes(formatId)) return <Smartphone className="w-4 h-4" />;
    if (['landscape', 'banner', 'twitter', 'linkedin', 'youtube'].includes(formatId)) return <Monitor className="w-4 h-4" />;
    if (formatId === 'square') return <Square className="w-4 h-4" />;
    return <ImageIcon className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-white">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Package className="w-5 h-5 text-green-400" />
              Multi-Format Export
            </h1>
            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
              Slice 11
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input & Format Selection */}
          <div className="space-y-6">
            {/* Ad Content */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Ad Content</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Image URL</label>
                  <input
                    type="url"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-green-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Headline</label>
                  <input
                    type="text"
                    value={headline}
                    onChange={(e) => setHeadline(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-green-500"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">CTA</label>
                    <input
                      type="text"
                      value={cta}
                      onChange={(e) => setCta(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Brand Name</label>
                    <input
                      type="text"
                      value={brandName}
                      onChange={(e) => setBrandName(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-green-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Format Selection */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Select Formats</h2>
                <button
                  onClick={toggleSelectAll}
                  className="text-sm text-green-400 hover:text-green-300"
                >
                  {selectAll ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                {availableFormats.map((format) => (
                  <button
                    key={format.id}
                    onClick={() => toggleFormat(format.id)}
                    className={`p-3 rounded-lg border text-left transition ${
                      selectedFormats.has(format.id)
                        ? 'border-green-500 bg-green-500/10'
                        : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        {getFormatIcon(format.id)}
                        <span className="font-medium">{format.name}</span>
                      </div>
                      {selectedFormats.has(format.id) && (
                        <Check className="w-4 h-4 text-green-400" />
                      )}
                    </div>
                    <div className="text-xs text-gray-400">
                      {format.width}×{format.height} • {format.aspect_ratio}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {format.platforms.slice(0, 2).join(', ')}
                    </div>
                  </button>
                ))}
              </div>
              
              <div className="mt-4 text-sm text-gray-400">
                {selectedFormats.size} of {availableFormats.length} formats selected
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleDemo}
                disabled={loading}
                className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium disabled:opacity-50 transition"
              >
                Run Demo
              </button>
              <button
                onClick={handleExport}
                disabled={loading || selectedFormats.size === 0 || !imageUrl || !headline}
                className="flex-1 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-400 hover:to-emerald-400 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Package className="w-5 h-5" />
                    Export {selectedFormats.size} Formats
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            {/* Error */}
            {error && (
              <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <p>{error}</p>
                </div>
              </div>
            )}

            {/* Placeholder */}
            {!result && !loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <FileImage className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No exports yet</h3>
                <p className="text-gray-500">Select formats and click "Export" to generate all sizes</p>
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Loader2 className="w-16 h-16 text-green-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">Exporting formats...</h3>
                <p className="text-gray-500">Generating {selectedFormats.size} ad sizes</p>
              </div>
            )}

            {/* Results */}
            {result && !loading && (
              <>
                {/* Summary Card */}
                <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 border border-green-500/30 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-green-400">Export Complete!</h3>
                    <span className="text-sm text-gray-400">{result.export_time_ms}ms</span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">{result.formats_exported}</div>
                      <div className="text-sm text-gray-400">Formats</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">{result.total_size_kb}</div>
                      <div className="text-sm text-gray-400">KB Total</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">{Math.round(result.total_size_kb / result.formats_exported)}</div>
                      <div className="text-sm text-gray-400">KB Avg</div>
                    </div>
                  </div>
                  
                  {result.zip_path && (
                    <a
                      href={`${API_BASE}${result.zip_path}`}
                      download
                      className="flex items-center justify-center gap-2 w-full py-3 bg-green-500 hover:bg-green-400 text-black font-medium rounded-lg transition"
                    >
                      <Archive className="w-5 h-5" />
                      Download All (ZIP)
                    </a>
                  )}
                </div>

                {/* Individual Files */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">Exported Files</h3>
                  
                  <div className="space-y-3">
                    {result.files.map((file) => (
                      <div
                        key={file.format}
                        className="flex items-center justify-between p-3 bg-gray-800 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          {getFormatIcon(file.format)}
                          <div>
                            <div className="font-medium">{file.name}</div>
                            <div className="text-xs text-gray-400">
                              {file.dimensions} • {file.size_kb} KB
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <a
                            href={`${API_BASE}${file.file_path}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 text-gray-400 hover:text-white transition"
                            title="Preview"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                          <a
                            href={`${API_BASE}${file.file_path}`}
                            download
                            className="p-2 text-green-400 hover:text-green-300 transition"
                            title="Download"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Preview Grid */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">Preview Grid</h3>
                  
                  <div className="grid grid-cols-3 gap-3">
                    {result.files.slice(0, 6).map((file) => (
                      <a
                        key={file.format}
                        href={`${API_BASE}${file.file_path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="relative aspect-square bg-gray-800 rounded-lg overflow-hidden hover:ring-2 ring-green-500 transition"
                      >
                        <img
                          src={`${API_BASE}${file.file_path}`}
                          alt={file.name}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1 text-xs">
                          {file.name}
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
