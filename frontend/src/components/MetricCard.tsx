import React from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  variant?: "default" | "primary" | "accent" | "danger" | "warning";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  variant = "default",
}) => {
  const borderClass = {
    default: "border-surface-border",
    primary: "border-primary/40 bg-primary/5",
    accent: "border-accent/40 bg-accent/5",
    danger: "border-danger/40 bg-danger/5",
    warning: "border-warning/40 bg-warning/5",
  }[variant];

  const valueClass = {
    default: "text-slate-100",
    primary: "text-primary",
    accent: "text-accent",
    danger: "text-danger",
    warning: "text-warning",
  }[variant];

  return (
    <div className={`rounded-xl border bg-surface p-5 shadow-sm transition-all hover:border-slate-600 ${borderClass}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {trend && <span className="text-xs font-mono font-medium text-slate-300">{trend}</span>}
      </div>
      <div className={`mt-3 text-3xl font-bold font-mono tracking-tight ${valueClass}`}>
        {value}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
};
