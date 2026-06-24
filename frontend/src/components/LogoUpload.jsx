import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Upload, 
  Image as ImageIcon, 
  Download, 
  Trash2, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Scissors,
  Sparkles
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';

export const LogoUpload = () => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [originalImage, setOriginalImage] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, completed, error
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        setError('Файл слишком большой. Максимальный размер: 10МБ');
        return;
      }
      
      setUploadedFile(file);
      setStatus('uploading');
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setOriginalImage(e.target.result);
        setStatus('idle');
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
    },
    multiple: false
  });

  const processBackgroundRemoval = async () => {
    if (!uploadedFile) return;
    
    setProcessing(true);
    setStatus('processing');
    setError(null);

    try {
      // Create FormData for API upload
      const formData = new FormData();
      formData.append('image', uploadedFile);
      formData.append('size', 'auto');
      formData.append('format', 'png');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/logo/remove-background`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Get processed image as blob
      const blob = await response.blob();
      const processedImageUrl = URL.createObjectURL(blob);
      
      setProcessedImage(processedImageUrl);
      setStatus('completed');
      
    } catch (err) {
      console.error('Background removal error:', err);
      setError('Ошибка обработки изображения. Попробуйте еще раз.');
      setStatus('error');
    } finally {
      setProcessing(false);
    }
  };

  const saveAsLogo = async () => {
    if (!processedImage) return;

    try {
      // Convert processed image to blob and send to backend
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = async () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        canvas.toBlob(async (blob) => {
          const formData = new FormData();
          formData.append('logo', blob, 'logo.png');
          
          const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/logo/save`, {
            method: 'POST',
            body: formData,
          });

          if (response.ok) {
            setStatus('saved');
            // Trigger logo refresh in parent components
            window.dispatchEvent(new CustomEvent('logoUpdated'));
          }
        }, 'image/png');
      };
      
      img.src = processedImage;
    } catch (err) {
      setError('Ошибка сохранения логотипа');
    }
  };

  const downloadProcessed = () => {
    if (processedImage) {
      const link = document.createElement('a');
      link.href = processedImage;
      link.download = 'logo-transparent.png';
      link.click();
    }
  };

  const resetUpload = () => {
    setUploadedFile(null);
    setOriginalImage(null);
    setProcessedImage(null);
    setStatus('idle');
    setError(null);
  };

  return (
    <div className="space-y-6">
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ImageIcon className="h-6 w-6 text-blue-600" />
            Загрузка и обработка логотипа
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {/* Upload Area */}
          <div 
            {...getRootProps()} 
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
              ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}
              ${status === 'uploading' ? 'opacity-50' : ''}
            `}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <Upload className="h-12 w-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-lg font-medium text-gray-700">
                  Перетащите файл логотипа или нажмите для выбора
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Поддерживаются: PNG, JPG, JPEG, GIF, SVG, WEBP (макс. 10МБ)
                </p>
              </div>
              {status === 'uploading' && (
                <Loader2 className="h-6 w-6 animate-spin text-blue-600 mx-auto" />
              )}
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Image Preview and Processing */}
          {originalImage && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Original Image */}
              <div className="space-y-3">
                <Label className="text-sm font-medium flex items-center gap-2">
                  <ImageIcon className="h-4 w-4" />
                  Оригинальное изображение
                </Label>
                <div className="border rounded-lg p-4 bg-checkered">
                  <img 
                    src={originalImage} 
                    alt="Original" 
                    className="max-w-full h-auto max-h-64 mx-auto object-contain"
                  />
                </div>
                <div className="text-xs text-gray-500 text-center">
                  {uploadedFile?.name} ({(uploadedFile?.size / 1024 / 1024).toFixed(1)}МБ)
                </div>
              </div>

              {/* Processed Image */}
              <div className="space-y-3">
                <Label className="text-sm font-medium flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  Обработанное изображение
                </Label>
                <div className="border rounded-lg p-4 bg-checkered min-h-[200px] flex items-center justify-center">
                  {processedImage ? (
                    <img 
                      src={processedImage} 
                      alt="Processed" 
                      className="max-w-full h-auto max-h-64 mx-auto object-contain"
                    />
                  ) : (
                    <div className="text-center text-gray-400">
                      <Scissors className="h-12 w-12 mx-auto mb-2" />
                      <p>Обработанное изображение появится здесь</p>
                    </div>
                  )}
                </div>
                
                {processing && (
                  <div className="text-center text-sm text-blue-600 flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Удаляем фон с помощью ИИ...
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {originalImage && (
            <div className="flex flex-wrap gap-3 justify-center">
              <Button 
                onClick={processBackgroundRemoval}
                disabled={processing || status === 'completed'}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {processing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Обработка...
                  </>
                ) : (
                  <>
                    <Scissors className="h-4 w-4 mr-2" />
                    Удалить фон
                  </>
                )}
              </Button>

              {processedImage && (
                <>
                  <Button 
                    onClick={downloadProcessed}
                    variant="outline"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Скачать PNG
                  </Button>
                  
                  <Button 
                    onClick={saveAsLogo}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Сохранить как логотип сайта
                  </Button>
                </>
              )}

              <Button 
                onClick={resetUpload}
                variant="outline"
                className="text-red-600 border-red-600 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Очистить
              </Button>
            </div>
          )}

          {status === 'saved' && (
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-700">
                Логотип успешно сохранен и будет отображаться на сайте!
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};