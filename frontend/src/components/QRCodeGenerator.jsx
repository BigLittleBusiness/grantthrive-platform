import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from './common/GrantThriveCard';

const QRCodeGenerator = ({ grant, onQRCodeGenerated }) => {
  const [qrCodeData, setQRCodeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedStyle, setSelectedStyle] = useState('professional');
  const [includeLogo, setIncludeLogo] = useState(true);
  const [previewMode, setPreviewMode] = useState(false);
  const [availableStyles, setAvailableStyles] = useState({});

  const styles = {
    professional: {
      name: 'Professional',
      description: 'Clean square modules in corporate blue',
      color: '#1e40af',
      preview: '⬛',
      bestFor: 'Official council communications, formal documents'
    },
    modern: {
      name: 'Modern', 
      description: 'Rounded modules in vibrant green',
      color: '#059669',
      preview: '🟢',
      bestFor: 'Community outreach, social media, youth programs'
    },
    elegant: {
      name: 'Elegant',
      description: 'Circular modules in sophisticated purple', 
      color: '#7c3aed',
      preview: '🟣',
      bestFor: 'Premium grants, cultural programs, special events'
    }
  };

  useEffect(() => {
    loadAvailableStyles();
  }, []);

  const loadAvailableStyles = async () => {
    try {
      // In production, this would fetch from API
      setAvailableStyles(styles);
    } catch (error) {
      console.error('Error loading QR code styles:', error);
    }
  };

  const generateQRCode = async (isPreview = false) => {
    if (!grant || !grant.grant_id) {
      alert('Grant information is required to generate QR code');
      return;
    }

    try {
      setLoading(true);
      
      const requestData = {
        grant_id: grant.grant_id,
        title: grant.title || grant.name,
        council_name: grant.council_name || 'Council',
        funding_amount: grant.funding_amount || grant.max_amount || 0,
        deadline: grant.deadline || grant.closing_date,
        style: selectedStyle,
        include_logo: includeLogo
      };

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock QR code data
      const mockQRData = {
        grant_id: grant.grant_id,
        qr_code_url: `https://grantthrive.com/static/qr_codes/grant_${grant.grant_id}_${Date.now()}.png`,
        target_url: `https://grantthrive.com/grants/${grant.grant_id}`,
        filename: `grant_${grant.grant_id}_qr_code.png`,
        style: selectedStyle,
        created_at: new Date().toISOString(),
        grant_title: requestData.title,
        council_name: requestData.council_name,
        file_size_kb: 45.2,
        preview_base64: isPreview ? 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==' : null
      };

      setQRCodeData(mockQRData);
      
      if (onQRCodeGenerated) {
        onQRCodeGenerated(mockQRData);
      }

      if (!isPreview) {
        alert('QR code generated successfully!');
      }

    } catch (error) {
      console.error('Error generating QR code:', error);
      alert('Error generating QR code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const downloadQRCode = () => {
    if (qrCodeData && qrCodeData.qr_code_url) {
      // Create download link
      const link = document.createElement('a');
      link.href = qrCodeData.qr_code_url;
      link.download = qrCodeData.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const copyQRCodeURL = () => {
    if (qrCodeData && qrCodeData.target_url) {
      navigator.clipboard.writeText(qrCodeData.target_url).then(() => {
        alert('Grant URL copied to clipboard!');
      }).catch(() => {
        alert('Failed to copy URL to clipboard');
      });
    }
  };

  const shareQRCode = () => {
    if (qrCodeData && navigator.share) {
      navigator.share({
        title: `${grant.title || grant.name} - Grant Application`,
        text: `Apply for this grant from ${grant.council_name || 'Council'}`,
        url: qrCodeData.target_url
      }).catch(console.error);
    } else {
      copyQRCodeURL();
    }
  };

  return (
    <div className="space-y-6">
      {/* QR Code Style Selection */}
      <Card>
        <CardHeader>
          <CardTitle>🎨 QR Code Style</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(styles).map(([styleKey, styleInfo]) => (
              <div
                key={styleKey}
                onClick={() => setSelectedStyle(styleKey)}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedStyle === styleKey
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-3 mb-2">
                  <div 
                    className="w-6 h-6 rounded"
                    style={{ backgroundColor: styleInfo.color }}
                  ></div>
                  <span className="font-medium">{styleInfo.name}</span>
                  {selectedStyle === styleKey && (
                    <span className="text-blue-600">✓</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-2">{styleInfo.description}</p>
                <p className="text-xs text-gray-500">
                  <strong>Best for:</strong> {styleInfo.bestFor}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={includeLogo}
                onChange={(e) => setIncludeLogo(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">Include GrantThrive logo</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Grant Information Preview */}
      <Card>
        <CardHeader>
          <CardTitle>📋 Grant Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div><strong>Grant:</strong> {grant?.title || grant?.name || 'Grant Program'}</div>
            <div><strong>Council:</strong> {grant?.council_name || 'Council'}</div>
            <div><strong>Funding:</strong> ${(grant?.funding_amount || grant?.max_amount || 0).toLocaleString()}</div>
            <div><strong>Deadline:</strong> {grant?.deadline || grant?.closing_date || 'Not specified'}</div>
            <div><strong>QR Code URL:</strong> https://grantthrive.com/grants/{grant?.grant_id}</div>
          </div>
        </CardContent>
      </Card>

      {/* QR Code Generation */}
      <Card>
        <CardHeader>
          <CardTitle>🔲 Generate QR Code</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex space-x-3">
              <button
                onClick={() => generateQRCode(true)}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                {loading ? 'Generating...' : '👁️ Preview'}
              </button>
              <button
                onClick={() => generateQRCode(false)}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Generating...' : '🔲 Generate QR Code'}
              </button>
            </div>

            {loading && (
              <div className="flex items-center space-x-2 text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm">Generating QR code...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Generated QR Code Display */}
      {qrCodeData && (
        <Card>
          <CardHeader>
            <CardTitle>✅ Generated QR Code</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* QR Code Image */}
              <div className="flex justify-center">
                <div className="bg-white p-6 rounded-lg border-2 border-gray-200 inline-block">
                  {qrCodeData.preview_base64 ? (
                    <img 
                      src={qrCodeData.preview_base64} 
                      alt="QR Code Preview"
                      className="w-48 h-48 object-contain"
                    />
                  ) : (
                    <div className="w-48 h-48 bg-gray-100 border-2 border-dashed border-gray-300 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-4xl mb-2">🔲</div>
                        <div className="text-sm text-gray-600">QR Code</div>
                        <div className="text-xs text-gray-500">{selectedStyle}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* QR Code Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Style:</strong> {qrCodeData.style}</div>
                  <div><strong>File Size:</strong> {qrCodeData.file_size_kb} KB</div>
                  <div><strong>Created:</strong> {new Date(qrCodeData.created_at).toLocaleString()}</div>
                  <div><strong>Target URL:</strong> 
                    <a href={qrCodeData.target_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline ml-1">
                      View Grant
                    </a>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={downloadQRCode}
                  className="px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700"
                >
                  📥 Download QR Code
                </button>
                <button
                  onClick={copyQRCodeURL}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                >
                  📋 Copy Grant URL
                </button>
                <button
                  onClick={shareQRCode}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700"
                >
                  📤 Share
                </button>
                <button
                  onClick={() => generateQRCode(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  🔄 Regenerate
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Usage Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>💡 How to Use QR Codes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-start space-x-2">
              <span className="text-blue-600">📱</span>
              <div>
                <strong>Mobile Applications:</strong> Applicants can scan the QR code with their phone camera to instantly access the grant application form.
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-green-600">📄</span>
              <div>
                <strong>Print Materials:</strong> Include QR codes on flyers, posters, brochures, and newsletters for easy digital access.
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-purple-600">💻</span>
              <div>
                <strong>Digital Sharing:</strong> Use QR codes in emails, social media posts, and websites to drive traffic to grant applications.
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-orange-600">🏢</span>
              <div>
                <strong>Events & Meetings:</strong> Display QR codes at community events, council meetings, and information sessions.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Best Practices */}
      <Card>
        <CardHeader>
          <CardTitle>🎯 QR Code Best Practices</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Design Tips:</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Use high contrast colors for better scanning</li>
                <li>• Ensure QR code is at least 2cm x 2cm when printed</li>
                <li>• Test QR codes before distributing</li>
                <li>• Include clear "Scan to Apply" instructions</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Placement Ideas:</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Council website homepage</li>
                <li>• Community notice boards</li>
                <li>• Local newspaper advertisements</li>
                <li>• Social media posts and stories</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QRCodeGenerator;

