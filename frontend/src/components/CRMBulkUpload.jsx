import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { 
  Upload, 
  FileSpreadsheet, 
  Users, 
  Brain,
  Download, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  BarChart3,
  Filter,
  Settings,
  Trash2,
  UserX
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';

export const CRMBulkUpload = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadResult, setUploadResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSettings, setUploadSettings] = useState({
    enhance_with_ai: true,
    market_research: true,
    classify_industries: true,
    deduplicate: true,
    source_name: 'bulk_upload'
  });
  const [statistics, setStatistics] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [selectedSegment, setSelectedSegment] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [segments, setSegments] = useState({});
  const [industries, setIndustries] = useState({});

  useEffect(() => {
    loadStatistics();
    loadSegmentsAndIndustries();
  }, []);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      await handleFileUpload(file);
    }
  }, [uploadSettings]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const handleFileUpload = async (file) => {
    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('enhance_with_ai', uploadSettings.enhance_with_ai);
      formData.append('market_research', uploadSettings.market_research);
      formData.append('classify_industries', uploadSettings.classify_industries);
      formData.append('deduplicate', uploadSettings.deduplicate);
      formData.append('source_name', uploadSettings.source_name);

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/bulk/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadResult(result);
        setActiveTab('results');
        await loadStatistics(); // Refresh statistics
      } else {
        throw new Error(result.detail || 'Upload failed');
      }
    } catch (error) {
      setUploadResult({
        success: false,
        message: `Ошибка загрузки: ${error.message}`,
        details: { errors: [error.message] }
      });
    } finally {
      setUploading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/bulk/statistics`);
      const data = await response.json();
      if (data.success) {
        setStatistics(data.statistics);
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  };

  const loadSegmentsAndIndustries = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/bulk/segments`);
      const data = await response.json();
      if (data.success) {
        setSegments(data.market_segments);
        setIndustries(data.industry_categories);
      }
    } catch (error) {
      console.error('Error loading segments:', error);
    }
  };

  const loadCompaniesByFilter = async (type, value) => {
    try {
      const endpoint = type === 'segment' 
        ? `/api/crm/bulk/companies/by-segment/${value}`
        : `/api/crm/bulk/companies/by-industry/${value}`;
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}${endpoint}`);
      const data = await response.json();
      if (data.success) {
        setCompanies(data.companies);
        setActiveTab('companies');
      }
    } catch (error) {
      console.error('Error loading companies:', error);
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/bulk/template`);
      const data = await response.json();
      
      if (data.success) {
        // Create CSV content
        const csvContent = data.sample_csv;
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'crm_bulk_upload_template.csv';
        link.click();
      }
    } catch (error) {
      console.error('Error downloading template:', error);
    }
  };

  const deleteCompany = async (companyId, companyName) => {
    if (!confirm(`Удалить компанию "${companyName}"?`)) return;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/bulk/companies/${companyId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setCompanies(companies.filter(c => c.id !== companyId));
        await loadStatistics();
      }
    } catch (error) {
      console.error('Error deleting company:', error);
    }
  };

  const unsubscribeCompany = async (companyId, companyName) => {
    if (!confirm(`Отписать компанию "${companyName}" от рассылки?`)) return;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/bulk/companies/${companyId}/unsubscribe`, {
        method: 'POST'
      });

      if (response.ok) {
        // Update company status locally
        setCompanies(companies.map(c => 
          c.id === companyId ? { ...c, status: 'unsubscribed' } : c
        ));
      }
    } catch (error) {
      console.error('Error unsubscribing company:', error);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="w-full max-w-6xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-6 w-6 text-blue-600" />
            Массовая загрузка клиентов CRM
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="upload">Загрузка</TabsTrigger>
              <TabsTrigger value="settings">Настройки</TabsTrigger>
              <TabsTrigger value="results">Результаты</TabsTrigger>
              <TabsTrigger value="statistics">Статистика</TabsTrigger>
              <TabsTrigger value="companies">Компании</TabsTrigger>
            </TabsList>

            {/* Upload Tab */}
            <TabsContent value="upload" className="space-y-6">
              
              {/* Template Download */}
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Загрузка данных</h3>
                <Button onClick={downloadTemplate} variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Скачать шаблон CSV
                </Button>
              </div>

              {/* Upload Area */}
              <div 
                {...getRootProps()} 
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
                  ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}
                  ${uploading ? 'opacity-50 pointer-events-none' : ''}
                `}
              >
                <input {...getInputProps()} />
                <div className="space-y-4">
                  <FileSpreadsheet className="h-16 w-16 text-gray-400 mx-auto" />
                  <div>
                    <p className="text-lg font-medium text-gray-700">
                      Перетащите CSV/Excel файл или нажмите для выбора
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      Поддерживаются: CSV, XLSX, XLS (макс. 50МБ)
                    </p>
                  </div>
                  {uploading && (
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-6 w-6 animate-spin text-blue-600 mr-2" />
                      <span className="text-blue-600">Загружаем и обрабатываем данные...</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Instructions */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Инструкция:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Обязательные поля: Название компании, Телефон, Email, Веб-сайт</li>
                  <li>• Дополнительные: Контактное лицо, Должность, Отдел, Мобильный</li>
                  <li>• ИИ автоматически улучшит данные и классифицирует отрасли</li>
                  <li>• Система найдет дубликаты и добавит новые контакты</li>
                </ul>
              </div>
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings" className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Настройки обработки
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="enhance_ai"
                            checked={uploadSettings.enhance_with_ai}
                            onChange={(e) => setUploadSettings({
                              ...uploadSettings, 
                              enhance_with_ai: e.target.checked
                            })}
                            className="rounded border-gray-300"
                          />
                          <Label htmlFor="enhance_ai" className="flex items-center gap-2">
                            <Brain className="h-4 w-4" />
                            Улучшение данных ИИ
                          </Label>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="market_research"
                            checked={uploadSettings.market_research}
                            onChange={(e) => setUploadSettings({
                              ...uploadSettings, 
                              market_research: e.target.checked
                            })}
                            className="rounded border-gray-300"
                          />
                          <Label htmlFor="market_research">Маркетинговые исследования</Label>
                        </div>

                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="classify_industries"
                            checked={uploadSettings.classify_industries}
                            onChange={(e) => setUploadSettings({
                              ...uploadSettings, 
                              classify_industries: e.target.checked
                            })}
                            className="rounded border-gray-300"
                          />
                          <Label htmlFor="classify_industries">Классификация отраслей</Label>
                        </div>

                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="deduplicate"
                            checked={uploadSettings.deduplicate}
                            onChange={(e) => setUploadSettings({
                              ...uploadSettings, 
                              deduplicate: e.target.checked
                            })}
                            className="rounded border-gray-300"
                          />
                          <Label htmlFor="deduplicate">Удаление дубликатов</Label>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="space-y-4">
                        <Label>Источник данных</Label>
                        <Input
                          value={uploadSettings.source_name}
                          onChange={(e) => setUploadSettings({
                            ...uploadSettings, 
                            source_name: e.target.value
                          })}
                          placeholder="bulk_upload"
                        />
                        <p className="text-xs text-gray-500">
                          Для отслеживания источника данных в CRM
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            {/* Results Tab */}
            <TabsContent value="results" className="space-y-6">
              {uploadResult && (
                <div className="space-y-4">
                  <Alert className={uploadResult.success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
                    {uploadResult.success ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <AlertDescription className={uploadResult.success ? "text-green-700" : "text-red-700"}>
                      {uploadResult.message}
                    </AlertDescription>
                  </Alert>

                  {uploadResult.details && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Card>
                        <CardContent className="pt-6 text-center">
                          <div className="text-2xl font-bold text-blue-600">
                            {uploadResult.details.total_rows}
                          </div>
                          <div className="text-sm text-gray-500">Строк в файле</div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardContent className="pt-6 text-center">
                          <div className="text-2xl font-bold text-green-600">
                            {uploadResult.details.new_companies}
                          </div>
                          <div className="text-sm text-gray-500">Новые компании</div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardContent className="pt-6 text-center">
                          <div className="text-2xl font-bold text-orange-600">
                            {uploadResult.details.updated_companies}
                          </div>
                          <div className="text-sm text-gray-500">Обновлено</div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardContent className="pt-6 text-center">
                          <div className="text-2xl font-bold text-purple-600">
                            {uploadResult.details.ai_enhancements}
                          </div>
                          <div className="text-sm text-gray-500">ИИ улучшения</div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {uploadResult.details?.errors && uploadResult.details.errors.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-red-600">Ошибки обработки</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-1">
                          {uploadResult.details.errors.map((error, index) => (
                            <li key={index} className="text-sm text-red-600">• {error}</li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </TabsContent>

            {/* Statistics Tab */}
            <TabsContent value="statistics" className="space-y-6">
              {statistics && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Статистика CRM
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="pt-6 text-center">
                        <div className="text-3xl font-bold text-blue-600">
                          {statistics.total_companies}
                        </div>
                        <div className="text-sm text-gray-500">Всего компаний</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6 text-center">
                        <div className="text-3xl font-bold text-green-600">
                          {statistics.bulk_uploaded}
                        </div>
                        <div className="text-sm text-gray-500">Загружено массово</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6 text-center">
                        <div className="text-3xl font-bold text-purple-600">
                          {statistics.ai_enhanced}
                        </div>
                        <div className="text-sm text-gray-500">С ИИ данными</div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Market Segments */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Сегменты рынка</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {Object.entries(statistics.by_market_segment || {}).map(([segment, count]) => (
                          <div key={segment} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <span className="text-sm">{segment}</span>
                            <Badge variant="secondary">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Industries */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Отрасли</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {Object.entries(statistics.by_industry || {}).map(([industry, count]) => (
                          <div key={industry} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <span className="text-sm">{industry}</span>
                            <Badge variant="secondary">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </TabsContent>

            {/* Companies Tab */}
            <TabsContent value="companies" className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Фильтр компаний
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>По сегменту рынка</Label>
                    <select 
                      className="w-full p-2 border rounded-lg"
                      value={selectedSegment}
                      onChange={(e) => {
                        setSelectedSegment(e.target.value);
                        if (e.target.value) {
                          loadCompaniesByFilter('segment', e.target.value);
                        }
                      }}
                    >
                      <option value="">Выберите сегмент</option>
                      {Object.entries(segments).map(([key, description]) => (
                        <option key={key} value={key}>{key} - {description}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <Label>По отрасли</Label>
                    <select 
                      className="w-full p-2 border rounded-lg"
                      value={selectedIndustry}
                      onChange={(e) => {
                        setSelectedIndustry(e.target.value);
                        if (e.target.value) {
                          loadCompaniesByFilter('industry', e.target.value);
                        }
                      }}
                    >
                      <option value="">Выберите отрасль</option>
                      {Object.entries(industries).map(([key, data]) => (
                        <option key={key} value={key}>{key}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Companies List */}
                {companies.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Компании ({companies.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4 max-h-96 overflow-y-auto">
                        {companies.map((company) => (
                          <div key={company.id} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <h4 className="font-medium">{company.company_name}</h4>
                                {company.website && (
                                  <p className="text-sm text-blue-600">{company.website}</p>
                                )}
                                {company.main_email && (
                                  <p className="text-sm text-gray-600">{company.main_email}</p>
                                )}
                                {company.description && (
                                  <p className="text-sm text-gray-500 mt-1">{company.description}</p>
                                )}
                                <div className="flex gap-2 mt-2">
                                  {company.market_segment && (
                                    <Badge variant="outline">{company.market_segment}</Badge>
                                  )}
                                  {company.industry_category && (
                                    <Badge variant="secondary">{company.industry_category}</Badge>
                                  )}
                                  {company.status === 'unsubscribed' && (
                                    <Badge variant="destructive">Отписан</Badge>
                                  )}
                                </div>
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => unsubscribeCompany(company.id, company.company_name)}
                                  disabled={company.status === 'unsubscribed'}
                                >
                                  <UserX className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => deleteCompany(company.id, company.company_name)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};