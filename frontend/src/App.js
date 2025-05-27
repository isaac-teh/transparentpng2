import React, { useState, useCallback } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BackgroundRemover = () => {
  const [originalImage, setOriginalImage] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processingStats, setProcessingStats] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [sliderPosition, setSliderPosition] = useState(50);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file');
      return;
    }

    // Validate file size (20MB limit)
    if (file.size > 20 * 1024 * 1024) {
      setError('File size must be less than 20MB');
      return;
    }

    setError(null);
    setLoading(true);
    setProcessedImage(null);
    setProcessingStats(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/remove-background-base64`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setOriginalImage(response.data.original_image);
      setProcessedImage(response.data.processed_image);
      setProcessingStats({
        processing_time: response.data.processing_time,
        original_size: response.data.original_size,
        processed_size: response.data.processed_size
      });

    } catch (err) {
      console.error('Processing failed:', err);
      setError(err.response?.data?.detail || 'Failed to process image');
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = () => {
    if (!processedImage) return;

    const link = document.createElement('a');
    link.href = processedImage;
    link.download = 'background_removed.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const resetImages = () => {
    setOriginalImage(null);
    setProcessedImage(null);
    setError(null);
    setProcessingStats(null);
    setSliderPosition(50);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🎨 AI Background Remover
          </h1>
          <p className="text-gray-600 text-lg">
            Remove image backgrounds instantly with AI - No external APIs, completely private
          </p>
        </div>

        {/* Upload Area */}
        {!originalImage && (
          <div className="mb-8">
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                dragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="space-y-4">
                <div className="text-6xl">📸</div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">
                    Drag & Drop Your Image Here
                  </h3>
                  <p className="text-gray-500 mb-4">
                    or click to browse files
                  </p>
                  <label className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors cursor-pointer">
                    Choose Image
                    <input
                      type="file"
                      className="hidden"
                      accept="image/*"
                      onChange={handleFileInput}
                    />
                  </label>
                </div>
                <p className="text-sm text-gray-400">
                  Supports JPEG, PNG, WebP • Max 20MB
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <span className="text-red-600 mr-2">⚠️</span>
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="mb-8 p-8 bg-white rounded-xl shadow-lg">
            <div className="text-center">
              <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                🧠 AI is removing the background...
              </h3>
              <p className="text-gray-500">
                This may take a few seconds depending on image size
              </p>
            </div>
          </div>
        )}

        {/* Results */}
        {originalImage && processedImage && (
          <div className="space-y-6">
            {/* Stats */}
            {processingStats && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-4">
                  ✨ Processing Complete
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-600">
                      {processingStats.processing_time.toFixed(2)}s
                    </div>
                    <div className="text-sm text-green-700">Processing Time</div>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-600">
                      {formatFileSize(processingStats.original_size)}
                    </div>
                    <div className="text-sm text-blue-700">Original Size</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-600">
                      {formatFileSize(processingStats.processed_size)}
                    </div>
                    <div className="text-sm text-purple-700">Result Size</div>
                  </div>
                </div>
              </div>
            )}

            {/* Before/After Comparison */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-4">
                🔄 Before vs After Comparison
              </h3>
              
              <div className="relative bg-white rounded-lg overflow-hidden border border-gray-200">
                {/* Images Container */}
                <div className="relative aspect-video bg-white">
                  {/* Processed Image (Background Removed) - LEFT SIDE - Full width with transparent pattern */}
                  <div className="absolute inset-0" style={{
                    backgroundImage: `url("data:image/svg+xml,%3csvg width='20' height='20' xmlns='http://www.w3.org/2000/svg'%3e%3cg fill='%23f0f0f0'%3e%3cpolygon points='0,0 0,10 10,10 10,0'/%3e%3cpolygon points='10,10 10,20 20,20 20,10'/%3e%3c/g%3e%3c/svg%3e")`,
                    backgroundSize: '20px 20px'
                  }}>
                    <img
                      src={processedImage}
                      alt="Background Removed"
                      className="w-full h-full object-contain"
                    />
                  </div>
                  
                  {/* Original Image Overlay - RIGHT SIDE - Dynamic width */}
                  <div 
                    className="absolute top-0 right-0 h-full overflow-hidden bg-white"
                    style={{ width: `${100 - sliderPosition}%` }}
                  >
                    <div className="relative w-full h-full">
                      <img
                        src={originalImage}
                        alt="Original"
                        className="absolute top-0 h-full object-contain"
                        style={{ 
                          right: 0,
                          width: `${(100 / (100 - sliderPosition)) * 100}%`,
                          transform: `translateX(${sliderPosition / (100 - sliderPosition) * 100}%)`
                        }}
                      />
                    </div>
                  </div>
                  
                  {/* Vertical Slider Line - GREEN */}
                  <div
                    className="absolute top-0 bottom-0 w-1 bg-green-500 shadow-lg z-20 pointer-events-none"
                    style={{ left: `${sliderPosition}%`, transform: 'translateX(-50%)' }}
                  >
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-green-500 rounded-full shadow-lg flex items-center justify-center border-2 border-white">
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                  </div>
                  
                  {/* Labels */}
                  <div className="absolute top-4 left-4 bg-green-600 bg-opacity-90 text-white px-3 py-1 rounded-lg text-sm font-bold">
                    Background Removed
                  </div>
                  <div className="absolute top-4 right-4 bg-black bg-opacity-80 text-white px-3 py-1 rounded-lg text-sm font-bold">
                    Original
                  </div>
                </div>
                
                {/* Slider Control */}
                <div className="mt-4">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={sliderPosition}
                    onChange={(e) => setSliderPosition(Number(e.target.value))}
                    className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer slider focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <div className="flex justify-between text-sm text-gray-600 mt-2 font-medium">
                    <span>← Background Removed</span>
                    <span className="text-center">Drag to Compare</span>
                    <span>Original →</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={downloadImage}
                className="px-8 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center"
              >
                <span className="mr-2">💾</span>
                Download PNG
              </button>
              <button
                onClick={resetImages}
                className="px-8 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors flex items-center justify-center"
              >
                <span className="mr-2">🔄</span>
                Process Another
              </button>
            </div>
          </div>
        )}

        {/* Features Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="text-4xl mb-4">🔒</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              100% Private
            </h3>
            <p className="text-gray-500">
              Images processed on your server. No external APIs or data sharing.
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Lightning Fast
            </h3>
            <p className="text-gray-500">
              AI-powered processing in seconds. No waiting, no limits.
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-6 text-center">
            <div className="text-4xl mb-4">💰</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Zero Cost
            </h3>
            <p className="text-gray-500">
              No per-image fees. Process unlimited images for free.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BackgroundRemover />
    </div>
  );
}

export default App;