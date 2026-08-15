import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function DashboardLayout({ title, subtitle, topbarChildren, children }) {
  return (
    <div className="flex bg-surface-page min-h-screen text-ink-hi font-body">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <Topbar title={title} subtitle={subtitle}>{topbarChildren}</Topbar>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
