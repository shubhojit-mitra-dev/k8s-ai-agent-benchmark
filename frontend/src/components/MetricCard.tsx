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
    default: "border-hairline bg-surface-card",
    primary: "border-primary/40 bg-surface-cream-strong",
    accent: "border-success/40 bg-surface-card",
    danger: "border-error/40 bg-surface-card",
    warning: "border-warning/40 bg-surface-card",
  }[variant];

  const valueClass = {
    default: "text-ink",
    primary: "text-primary",
    accent: "text-success",
    danger: "text-error",
    warning: "text-warning",
  }[variant];

  return (
    <div className={`rounded-lg border p-5 shadow-sm transition-all hover:border-muted-soft ${borderClass}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted font-sans">{title}</span>
        {trend && <span className="text-xs font-mono font-medium text-body-strong bg-surface-soft px-2 py-0.5 rounded border border-hairline">{trend}</span>}
      </div>
      <div className={`mt-2.5 text-3xl font-medium font-serif tracking-tight ${valueClass}`}>
        {value}
      </div>
      {subtitle && <p className="mt-1 text-xs text-body font-sans">{subtitle}</p>}
    </div>
  );
};
