import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '../components/common/GrantThriveCard';

const CommunicationSettings = () => {
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingNotification, setTestingNotification] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [activeTab, setActiveTab] = useState('preferences');

  // Mock council ID - in production, get from auth context
  const councilId = 'council_001';

  const eventTypes = [
    { value: 'application_received', display: 'Application Received' },
    { value: 'application_approved', display: 'Application Approved' },
    { value: 'application_rejected', display: 'Application Rejected' },
    { value: 'deadline_reminder', display: 'Deadline Reminder' },
    { value: 'document_required', display: 'Document Required' },
    { value: 'payment_processed', display: 'Payment Processed' },
    { value: 'report_due', display: 'Report Due' },
    { value: 'meeting_reminder', display: 'Meeting Reminder' },
    { value: 'general_update', display: 'General Update' }
  ];

  const communicationTypes = [
    { value: 'email', display: 'Email Only', icon: '📧' },
    { value: 'sms', display: 'SMS Only', icon: '📱' },
    { value: 'both', display: 'Both Email & SMS', icon: '📧📱' },
    { value: 'none', display: 'No Communication', icon: '🚫' }
  ];

  const smsProviders = [
    { value: 'twilio', display: 'Twilio' },
    { value: 'messagemedia', display: 'MessageMedia (Australian)' },
    { value: 'clicksend', display: 'ClickSend' }
  ];

  useEffect(() => {
    loadPreferences();
    loadStatistics();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      // Simulate API call
      const mockPreferences = {
        council_id: councilId,
        email_enabled: true,
        sms_enabled: true,
        sms_provider: 'twilio',
        allow_applicant_override: true,
        business_hours_only_sms: true,
        business_hours: '8:00 - 18:00',
        timezone: 'Australia/Sydney',
        sms_daily_limit: 1000,
        sms_monthly_budget: 500.00,
        preferences: {
          application_received: { communication_type: 'email', will_send_email: true, will_send_sms: false },
          application_approved: { communication_type: 'both', will_send_email: true, will_send_sms: true },
          application_rejected: { communication_type: 'email', will_send_email: true, will_send_sms: false },
          deadline_reminder: { communication_type: 'sms', will_send_email: false, will_send_sms: true },
          document_required: { communication_type: 'email', will_send_email: true, will_send_sms: false },
          payment_processed: { communication_type: 'both', will_send_email: true, will_send_sms: true },
          report_due: { communication_type: 'email', will_send_email: true, will_send_sms: false },
          meeting_reminder: { communication_type: 'sms', will_send_email: false, will_send_sms: true },
          general_update: { communication_type: 'email', will_send_email: true, will_send_sms: false }
        }
      };
      setPreferences(mockPreferences);
    } catch (error) {
      console.error('Error loading preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      // Simulate API call for statistics
      const mockStats = {
        total_notifications: 1247,
        emails_sent: 892,
        sms_sent: 355,
        successful_deliveries: 1198,
        failed_deliveries: 49,
        by_event_type: {
          application_received: 245,
          application_approved: 89,
          application_rejected: 156,
          deadline_reminder: 423,
          document_required: 178,
          payment_processed: 89,
          report_due: 67
        },
        by_preference: {
          email: 567,
          sms: 234,
          both: 446
        }
      };
      setStatistics(mockStats);
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  };

  const updatePreference = (eventType, communicationType) => {
    setPreferences(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [eventType]: {
          ...prev.preferences[eventType],
          communication_type: communicationType,
          will_send_email: ['email', 'both'].includes(communicationType),
          will_send_sms: ['sms', 'both'].includes(communicationType)
        }
      }
    }));
  };

  const updateGlobalSetting = (setting, value) => {
    setPreferences(prev => ({
      ...prev,
      [setting]: value
    }));
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('Communication preferences saved successfully!');
    } catch (error) {
      console.error('Error saving preferences:', error);
      alert('Error saving preferences. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const testNotification = async (testType) => {
    try {
      setTestingNotification(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert(`Test ${testType} notification sent successfully!`);
    } catch (error) {
      console.error('Error sending test notification:', error);
      alert('Error sending test notification. Please try again.');
    } finally {
      setTestingNotification(false);
    }
  };

  const resetToDefaults = async () => {
    if (window.confirm('Are you sure you want to reset all communication preferences to defaults?')) {
      try {
        setSaving(true);
        await loadPreferences(); // Reload default preferences
        alert('Communication preferences reset to defaults!');
      } catch (error) {
        console.error('Error resetting preferences:', error);
        alert('Error resetting preferences. Please try again.');
      } finally {
        setSaving(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading communication settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Communication Settings</h1>
        <p className="text-gray-600">
          Configure how GrantThrive communicates with grant applicants. Choose between email, SMS, or both for different types of notifications.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'preferences', label: 'Notification Preferences', icon: '⚙️' },
              { id: 'global', label: 'Global Settings', icon: '🌐' },
              { id: 'statistics', label: 'Statistics', icon: '📊' },
              { id: 'test', label: 'Test Notifications', icon: '🧪' }
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

        <div className="p-6">
          {/* Notification Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900">Event-Specific Communication Preferences</h2>
                <div className="space-x-3">
                  <button
                    onClick={resetToDefaults}
                    disabled={saving}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Reset to Defaults
                  </button>
                  <button
                    onClick={savePreferences}
                    disabled={saving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                  {communicationTypes.map(type => (
                    <div key={type.value} className="text-center p-3 bg-white rounded-lg border">
                      <div className="text-2xl mb-2">{type.icon}</div>
                      <div className="text-sm font-medium text-gray-900">{type.display}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                {eventTypes.map(event => (
                  <div key={event.value} className="bg-white border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{event.display}</h3>
                        <p className="text-sm text-gray-500 mt-1">
                          Current setting: {preferences?.preferences[event.value]?.will_send_email && preferences?.preferences[event.value]?.will_send_sms ? 'Email & SMS' :
                          preferences?.preferences[event.value]?.will_send_email ? 'Email Only' :
                          preferences?.preferences[event.value]?.will_send_sms ? 'SMS Only' : 'No Communication'}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        {communicationTypes.map(type => (
                          <button
                            key={type.value}
                            onClick={() => updatePreference(event.value, type.value)}
                            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                              preferences?.preferences[event.value]?.communication_type === type.value
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            {type.icon} {type.display}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Global Settings Tab */}
          {activeTab === 'global' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900">Global Communication Settings</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Email Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle>📧 Email Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-gray-700">Enable Email Notifications</label>
                      <input
                        type="checkbox"
                        checked={preferences?.email_enabled}
                        onChange={(e) => updateGlobalSetting('email_enabled', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* SMS Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle>📱 SMS Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-gray-700">Enable SMS Notifications</label>
                      <input
                        type="checkbox"
                        checked={preferences?.sms_enabled}
                        onChange={(e) => updateGlobalSetting('sms_enabled', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">SMS Provider</label>
                      <select
                        value={preferences?.sms_provider}
                        onChange={(e) => updateGlobalSetting('sms_provider', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      >
                        {smsProviders.map(provider => (
                          <option key={provider.value} value={provider.value}>
                            {provider.display}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-gray-700">Business Hours Only</label>
                      <input
                        type="checkbox"
                        checked={preferences?.business_hours_only_sms}
                        onChange={(e) => updateGlobalSetting('business_hours_only_sms', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Daily SMS Limit</label>
                      <input
                        type="number"
                        value={preferences?.sms_daily_limit}
                        onChange={(e) => updateGlobalSetting('sms_daily_limit', parseInt(e.target.value))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Monthly SMS Budget (AUD)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={preferences?.sms_monthly_budget}
                        onChange={(e) => updateGlobalSetting('sms_monthly_budget', parseFloat(e.target.value))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Applicant Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle>👥 Applicant Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-gray-700">Allow Applicant Preference Override</label>
                      <input
                        type="checkbox"
                        checked={preferences?.allow_applicant_override}
                        onChange={(e) => updateGlobalSetting('allow_applicant_override', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    </div>
                    <p className="text-xs text-gray-500">
                      When enabled, applicants can choose their preferred communication method
                    </p>
                  </CardContent>
                </Card>

                {/* Timezone Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle>🌐 Timezone Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
                      <select
                        value={preferences?.timezone}
                        onChange={(e) => updateGlobalSetting('timezone', e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      >
                        <option value="Australia/Sydney">Australia/Sydney</option>
                        <option value="Australia/Melbourne">Australia/Melbourne</option>
                        <option value="Australia/Brisbane">Australia/Brisbane</option>
                        <option value="Australia/Perth">Australia/Perth</option>
                        <option value="Australia/Adelaide">Australia/Adelaide</option>
                        <option value="Pacific/Auckland">New Zealand/Auckland</option>
                      </select>
                    </div>
                    <p className="text-xs text-gray-500">
                      Business hours: {preferences?.business_hours}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={savePreferences}
                  disabled={saving}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Global Settings'}
                </button>
              </div>
            </div>
          )}

          {/* Statistics Tab */}
          {activeTab === 'statistics' && statistics && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900">Communication Statistics</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="text-center p-6">
                    <div className="text-3xl font-bold text-blue-600">{statistics.total_notifications}</div>
                    <div className="text-sm text-gray-600">Total Notifications</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="text-center p-6">
                    <div className="text-3xl font-bold text-green-600">{statistics.emails_sent}</div>
                    <div className="text-sm text-gray-600">Emails Sent</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="text-center p-6">
                    <div className="text-3xl font-bold text-purple-600">{statistics.sms_sent}</div>
                    <div className="text-sm text-gray-600">SMS Sent</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="text-center p-6">
                    <div className="text-3xl font-bold text-orange-600">{statistics.successful_deliveries}</div>
                    <div className="text-sm text-gray-600">Successful Deliveries</div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Notifications by Event Type</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(statistics.by_event_type).map(([event, count]) => (
                        <div key={event} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 capitalize">
                            {event.replace('_', ' ')}
                          </span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Notifications by Preference</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(statistics.by_preference).map(([pref, count]) => (
                        <div key={pref} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 capitalize">{pref}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* Test Notifications Tab */}
          {activeTab === 'test' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900">Test Notifications</h2>
              <p className="text-gray-600">
                Send test notifications to verify your communication settings are working correctly.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>📧 Test Email</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <input
                      type="email"
                      placeholder="test@example.com"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                    <button
                      onClick={() => testNotification('email')}
                      disabled={testingNotification}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                    >
                      {testingNotification ? 'Sending...' : 'Send Test Email'}
                    </button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>📱 Test SMS</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <input
                      type="tel"
                      placeholder="+61 4XX XXX XXX"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                    <button
                      onClick={() => testNotification('sms')}
                      disabled={testingNotification}
                      className="w-full px-4 py-2 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
                    >
                      {testingNotification ? 'Sending...' : 'Send Test SMS'}
                    </button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>📧📱 Test Both</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <input
                      type="email"
                      placeholder="test@example.com"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm mb-2"
                    />
                    <input
                      type="tel"
                      placeholder="+61 4XX XXX XXX"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                    <button
                      onClick={() => testNotification('both')}
                      disabled={testingNotification}
                      className="w-full px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                    >
                      {testingNotification ? 'Sending...' : 'Send Test Both'}
                    </button>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CommunicationSettings;

