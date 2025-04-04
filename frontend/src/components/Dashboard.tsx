import { Activity, FileText, Link as LinkIcon, MessageSquare } from "lucide-react";
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

// Mock data for charts - replace with real data later
const usageData = [
  { name: "Mon", chats: 12, documents: 3, links: 2 },
  { name: "Tue", chats: 19, documents: 5, links: 3 },
  { name: "Wed", chats: 15, documents: 4, links: 1 },
  { name: "Thu", chats: 8, documents: 2, links: 4 },
  { name: "Fri", chats: 10, documents: 3, links: 2 },
  { name: "Sat", chats: 5, documents: 1, links: 1 },
  { name: "Sun", chats: 7, documents: 2, links: 3 },
];

export default function Dashboard({ documents, links }: DashboardProps) {
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
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">+12% from last week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{documents.length}</div>
            <p className="text-xs text-muted-foreground">+3 new this week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Links</CardTitle>
            <LinkIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{links.length}</div>
            <p className="text-xs text-muted-foreground">+5 new this week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">Currently online</p>
          </CardContent>
        </Card>
      </div>

      {/* Usage Statistics */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Weekly Activity</CardTitle>
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
                  <p className="text-xs text-muted-foreground">Response time: 120ms</p>
                </div>
                <div className="h-2 w-2 rounded-full bg-green-500" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Memory Usage</p>
                  <p className="text-xs text-muted-foreground">45% of 8GB</p>
                </div>
                <div className="h-2 w-2 rounded-full bg-yellow-500" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Storage</p>
                  <p className="text-xs text-muted-foreground">2.3GB of 10GB used</p>
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
                  <p className="text-xs text-muted-foreground">Uploaded 2 hours ago</p>
                </div>
              </div>
            ))}
            {links.slice(0, 3).map((link) => (
              <div key={link.id} className="flex items-center gap-4">
                <LinkIcon className="h-4 w-4 text-muted-foreground" />
                <div className="space-y-1">
                  <p className="text-sm font-medium">{link.title}</p>
                  <p className="text-xs text-muted-foreground">Added 1 day ago</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 