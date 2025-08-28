import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '../components/common/GrantThriveCard';
import QRCodeGenerator from '../components/QRCodeGenerator';

const QRCodeManagement = ({ user, onNavigate, onLogout }) => {
  const [activeTab, setActiveTab] = useState('generate');
  const [grants, setGrants] = useState([]);
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [qrCodes, setQRCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bulkGenerating, setBulkGenerating] = useState(false);

  // Mock grants data
  const mockGrants = [
    {
      grant_id: 'GRANT-001',
      title: 'Community Infrastructure Grant',
      council_name: 'City of Melbourne',
      funding_amount: 50000,
      deadline: '2024-12-31',
      status: 'active',
      applications_count: 23
    },
    {
      grant_id: 'GRANT-002', 
      title: 'Youth Development Program',
      council_name: 'City of Melbourne',
      funding_amount: 25000,
      deadline: '2024-11-30',
      status: 'active',
      applications_count: 15
    },
    {
      grant_id: 'GRANT-003',
      title: 'Environmental Sustainability Initiative',
      council_name: 'City of Melbourne', 
      funding_amount: 75000,
      deadline: '2025-01-15',
      status: 'draft',
      applications_count: 0
    }
  ];

  // Mock existing QR codes
  const mockQRCodes = [
    {
      grant_id: 'GRANT-001',
      grant_title: 'Community Infrastructure Grant',
      qr_code_url: 'https://grantthrive.com/static/qr_codes/grant_001_qr.png',
      style: 'professional',
      created_at: '2024-08-20T10:30:00Z',
      scans: 156,
      applications_from_qr: 23
    },
    {
      grant_id: 'GRANT-002',
      grant_title: 'Youth Development Program', 
      qr_code_url: 'https://grantthrive.com/static/qr_codes/grant_002_qr.png',
      style: 'modern',
      created_at: '2024-08-18T14:15:00Z',
      scans: 89,
      applications_from_qr: 15
    }
  ];

  useEffect(() => {
    loadGrants();
    loadQRCodes();
  }, []);

  const loadGrants = async () => {
    try {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      setGrants(mockGrants);
    } catch (error) {
      console.error('Error loading grants:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQRCodes = async () => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));
      setQRCodes(mockQRCodes);
    } catch (error) {
      console.error('Error loading QR codes:', error);
    }
  };

  const handleQRCodeGenerated = (qrCodeData) => {
    // Add new QR code to list
    setQRCodes(prev => [
      {
        ...qrCodeData,
        scans: 0,
        applications_from_qr: 0
      },
      ...prev.filter(qr => qr.grant_id !== qrCodeData.grant_id)
    ]);
  };

  const generateBulkQRCodes = async () => {
    try {
      setBulkGenerating(true);
      
      // Simulate bulk generation
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Generate QR codes for all active grants without existing QR codes
      const grantsNeedingQR = grants.filter(grant => 
        grant.status === 'active' && 
        !qrCodes.some(qr => qr.grant_id === grant.grant_id)
      );

      const newQRCodes = grantsNeedingQR.map(grant => ({
        grant_id: grant.grant_id,
        grant_title: grant.title,
        qr_code_url: `https://grantthrive.com/static/qr_codes/grant_${grant.grant_id}_qr.png`,
        style: 'professional',
        created_at: new Date().toISOString(),
        scans: 0,
        applications_from_qr: 0
      }));

      setQRCodes(prev => [...newQRCodes, ...prev]);
      alert(`Successfully generated ${newQRCodes.length} QR codes!`);

    } catch (error) {
      console.error('Error generating bulk QR codes:', error);
      alert('Error generating bulk QR codes. Please try again.');
    } finally {
      setBulkGenerating(false);
    }
  };

  const downloadAllQRCodes = async () => {
    try {
      // Simulate creating ZIP file
      alert('Preparing ZIP file with all QR codes...');
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // In production, this would trigger actual download
      alert('QR codes ZIP file downloaded successfully!');
    } catch (error) {
      console.error('Error downloading QR codes:', error);
      alert('Error downloading QR codes. Please try again.');
    }
  };

  const deleteQRCode = async (grantId) => {
    if (window.confirm('Are you sure you want to delete this QR code?')) {
      setQRCodes(prev => prev.filter(qr => qr.grant_id !== grantId));
      alert('QR code deleted successfully!');
    }
  };

  const regenerateQRCode = async (grant) => {
    try {
      setLoading(true);
      
      // Simulate regeneration
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const newQRCode = {
        grant_id: grant.grant_id,
        grant_title: grant.title,
        qr_code_url: `https://grantthrive.com/static/qr_codes/grant_${grant.grant_id}_${Date.now()}_qr.png`,
        style: 'professional',
        created_at: new Date().toISOString(),
        scans: 0,
        applications_from_qr: 0
      };

      setQRCodes(prev => [
        newQRCode,
        ...prev.filter(qr => qr.grant_id !== grant.grant_id)
      ]);

      alert('QR code regenerated successfully!');
    } catch (error) {
      console.error('Error regenerating QR code:', error);
      alert('Error regenerating QR code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">QR Code Management</h1>
              <p className="text-gray-600">Generate and manage QR codes for your grant programs</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                ← Back to Dashboard
              </button>
              <button
                onClick={onLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'generate', label: 'Generate QR Codes', icon: '🔲' },
                { id: 'manage', label: 'Manage Existing', icon: '📋' },
                { id: 'analytics', label: 'Analytics', icon: '📊' },
                { id: 'bulk', label: 'Bulk Operations', icon: '⚡' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Generate QR Codes Tab */}
        {activeTab === 'generate' && (
          <div className="space-y-6">
            {/* Grant Selection */}
            <Card>
              <CardHeader>
                <CardTitle>📝 Select Grant Program</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {grants.map(grant => (
                    <div
                      key={grant.grant_id}
                      onClick={() => setSelectedGrant(grant)}
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedGrant?.grant_id === grant.grant_id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-medium text-gray-900">{grant.title}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          grant.status === 'active' 
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {grant.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>💰 ${grant.funding_amount.toLocaleString()}</div>
                        <div>📅 {grant.deadline}</div>
                        <div>📊 {grant.applications_count} applications</div>
                      </div>
                      {selectedGrant?.grant_id === grant.grant_id && (
                        <div className="mt-2 text-blue-600 text-sm font-medium">
                          ✓ Selected for QR code generation
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* QR Code Generator */}
            {selectedGrant && (
              <QRCodeGenerator 
                grant={selectedGrant} 
                onQRCodeGenerated={handleQRCodeGenerated}
              />
            )}
          </div>
        )}

        {/* Manage Existing QR Codes Tab */}
        {activeTab === 'manage' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>📋 Existing QR Codes</CardTitle>
              </CardHeader>
              <CardContent>
                {qrCodes.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🔲</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No QR Codes Generated</h3>
                    <p className="text-gray-600 mb-4">Generate your first QR code to get started</p>
                    <button
                      onClick={() => setActiveTab('generate')}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                    >
                      Generate QR Code
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {qrCodes.map(qrCode => (
                      <div key={qrCode.grant_id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className="w-16 h-16 bg-gray-100 border-2 border-dashed border-gray-300 rounded flex items-center justify-center">
                              <span className="text-2xl">🔲</span>
                            </div>
                            <div>
                              <h3 className="font-medium text-gray-900">{qrCode.grant_title}</h3>
                              <div className="text-sm text-gray-600 space-y-1">
                                <div>Style: {qrCode.style}</div>
                                <div>Created: {new Date(qrCode.created_at).toLocaleDateString()}</div>
                                <div>Scans: {qrCode.scans} | Applications: {qrCode.applications_from_qr}</div>
                              </div>
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => window.open(qrCode.qr_code_url, '_blank')}
                              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              View
                            </button>
                            <button
                              onClick={() => {
                                const link = document.createElement('a');
                                link.href = qrCode.qr_code_url;
                                link.download = `${qrCode.grant_id}_qr_code.png`;
                                link.click();
                              }}
                              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                            >
                              Download
                            </button>
                            <button
                              onClick={() => {
                                const grant = grants.find(g => g.grant_id === qrCode.grant_id);
                                if (grant) regenerateQRCode(grant);
                              }}
                              className="px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700"
                            >
                              Regenerate
                            </button>
                            <button
                              onClick={() => deleteQRCode(qrCode.grant_id)}
                              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="text-center p-6">
                  <div className="text-3xl font-bold text-blue-600">{qrCodes.length}</div>
                  <div className="text-sm text-gray-600">Total QR Codes</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="text-center p-6">
                  <div className="text-3xl font-bold text-green-600">
                    {qrCodes.reduce((sum, qr) => sum + qr.scans, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Total Scans</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="text-center p-6">
                  <div className="text-3xl font-bold text-purple-600">
                    {qrCodes.reduce((sum, qr) => sum + qr.applications_from_qr, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Applications from QR</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="text-center p-6">
                  <div className="text-3xl font-bold text-orange-600">
                    {qrCodes.length > 0 ? 
                      Math.round((qrCodes.reduce((sum, qr) => sum + qr.applications_from_qr, 0) / 
                                 qrCodes.reduce((sum, qr) => sum + qr.scans, 0)) * 100) || 0 : 0}%
                  </div>
                  <div className="text-sm text-gray-600">Conversion Rate</div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>📊 QR Code Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {qrCodes.map(qrCode => (
                    <div key={qrCode.grant_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="font-medium">{qrCode.grant_title}</h3>
                        <span className="text-sm text-gray-600">
                          {Math.round((qrCode.applications_from_qr / Math.max(qrCode.scans, 1)) * 100)}% conversion
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-600">Scans</div>
                          <div className="font-medium">{qrCode.scans}</div>
                        </div>
                        <div>
                          <div className="text-gray-600">Applications</div>
                          <div className="font-medium">{qrCode.applications_from_qr}</div>
                        </div>
                        <div>
                          <div className="text-gray-600">Created</div>
                          <div className="font-medium">{new Date(qrCode.created_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Bulk Operations Tab */}
        {activeTab === 'bulk' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>⚡ Bulk QR Code Operations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="border rounded-lg p-4">
                      <h3 className="font-medium text-gray-900 mb-2">🔲 Generate All QR Codes</h3>
                      <p className="text-sm text-gray-600 mb-4">
                        Generate QR codes for all active grants that don't have one yet.
                      </p>
                      <button
                        onClick={generateBulkQRCodes}
                        disabled={bulkGenerating}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                      >
                        {bulkGenerating ? 'Generating...' : 'Generate All QR Codes'}
                      </button>
                    </div>

                    <div className="border rounded-lg p-4">
                      <h3 className="font-medium text-gray-900 mb-2">📥 Download All QR Codes</h3>
                      <p className="text-sm text-gray-600 mb-4">
                        Download a ZIP file containing all generated QR codes.
                      </p>
                      <button
                        onClick={downloadAllQRCodes}
                        disabled={qrCodes.length === 0}
                        className="w-full px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                      >
                        Download All QR Codes
                      </button>
                    </div>
                  </div>

                  {bulkGenerating && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span className="text-blue-800 font-medium">Generating QR codes...</span>
                      </div>
                      <p className="text-blue-700 text-sm mt-2">
                        This may take a few moments. Please don't close this page.
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>📋 Bulk Generation Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{grants.length}</div>
                    <div className="text-sm text-gray-600">Total Grants</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{qrCodes.length}</div>
                    <div className="text-sm text-gray-600">QR Codes Generated</div>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {grants.filter(g => g.status === 'active' && !qrCodes.some(qr => qr.grant_id === g.grant_id)).length}
                    </div>
                    <div className="text-sm text-gray-600">Pending Generation</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default QRCodeManagement;

