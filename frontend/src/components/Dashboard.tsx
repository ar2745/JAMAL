import { Activity, FileText, Link as LinkIcon, MessageSquare } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { ChartContainer, ChartLegend, ChartTooltip, ChartTooltipContent } from "./ui/chart";

interface DashboardProps {
  documents: Array<{
    id: string;
    name: string;
    content: string;
    type: string;
    selected?: boolean;
  }>;
  links: Array<{
    id: string;
    url: string;
    title: string;
    description?: string;
    content?: string;
    selected?: boolean;
  }>;
}

interface AnalyticsData {
  chatStats: {
    total_chats: number;
    total_messages: number;
    active_chats: number;
    total_active_users: number;
  };
  documentStats: {
    total_documents: number;
    total_size: number;
    types: Record<string, number>;
  };
  linkStats: {
    total_links: number;
    domains: Record<string, number>;
  };
  usageStats: {
    daily_active_users: number;
    weekly_active_users: number;
    monthly_active_users: number;
    concurrent_users: number;
    peak_hours: number[];
    average_response_time: number;
  };
}

export default function Dashboard({ documents, links }: DashboardProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        const [chatResponse, documentResponse, linkResponse, usageResponse] = await Promise.all([
          fetch('http://localhost:5000/analytics/chat'),
          fetch('http://localhost:5000/analytics/documents'),
          fetch('http://localhost:5000/analytics/links'),
          fetch('http://localhost:5000/analytics/usage')
        ]);

        const [chatStats, documentStats, linkStats, usageStats] = await Promise.all([
          chatResponse.json(),
          documentResponse.json(),
          linkResponse.json(),
          usageResponse.json()
        ]);

        setAnalyticsData({
          chatStats,
          documentStats,
          linkStats,
          usageStats
        });
      } catch (error) {
        console.error('Error fetching analytics data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchAnalyticsData, 120000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !analyticsData) {
    return <div className="p-6">Loading analytics data...</div>;
  }

  // Transform usage data for the chart
  const usageData = Object.entries(analyticsData.usageStats.peak_hours).map(([hour, count]) => ({
    name: `${hour}:00`,
    chats: count,
    documents: analyticsData.documentStats.types[hour] || 0,
    links: analyticsData.linkStats.domains[hour] || 0
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Chats</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.chatStats.total_chats}</div>
            <p className="text-xs text-muted-foreground">{analyticsData.chatStats.active_chats} active chats</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.documentStats.total_documents}</div>
            <p className="text-xs text-muted-foreground">{(analyticsData.documentStats.total_size / 1024 / 1024).toFixed(2)} MB total</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Links</CardTitle>
            <LinkIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.linkStats.total_links}</div>
            <p className="text-xs text-muted-foreground">{Object.keys(analyticsData.linkStats.domains).length} unique domains</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.usageStats.concurrent_users}</div>
            <p className="text-xs text-muted-foreground">{analyticsData.usageStats.daily_active_users} daily active</p>
          </CardContent>
        </Card>
      </div>

      {/* Usage Statistics */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Hourly Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{
              chats: { label: "Chats", color: "#3b82f6" },
              documents: { label: "Documents", color: "#10b981" },
              links: { label: "Links", color: "#8b5cf6" }
            }}>
              <BarChart data={usageData}>
                <XAxis dataKey="name" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend />
                <Bar dataKey="chats" fill="#3b82f6" />
                <Bar dataKey="documents" fill="#10b981" />
                <Bar dataKey="links" fill="#8b5cf6" />
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Backend API</p>
                  <p className="text-xs text-muted-foreground">Response time: {analyticsData.usageStats.average_response_time.toFixed(2)}ms</p>
                </div>
                <div className={`h-2 w-2 rounded-full ${analyticsData.usageStats.average_response_time < 200 ? 'bg-green-500' : 'bg-yellow-500'}`} />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Active Users</p>
                  <p className="text-xs text-muted-foreground">{analyticsData.usageStats.weekly_active_users} weekly active</p>
                </div>
                <div className="h-2 w-2 rounded-full bg-green-500" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Storage</p>
                  <p className="text-xs text-muted-foreground">{(analyticsData.documentStats.total_size / 1024 / 1024).toFixed(2)} MB used</p>
                </div>
                <div className="h-2 w-2 rounded-full bg-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {documents.slice(0, 3).map((doc) => (
              <div key={doc.id} className="flex items-center gap-4">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div className="space-y-1">
                  <p className="text-sm font-medium">{doc.name}</p>
                  <p className="text-xs text-muted-foreground">{doc.type}</p>
                </div>
              </div>
            ))}
            {links.slice(0, 3).map((link) => (
              <div key={link.id} className="flex items-center gap-4">
                <LinkIcon className="h-4 w-4 text-muted-foreground" />
                <div className="space-y-1">
                  <p className="text-sm font-medium">{link.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {link.url ? (() => {
                      try {
                        return new URL(link.url).hostname;
                      } catch (e) {
                        return link.url;
                      }
                    })() : 'No URL'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 