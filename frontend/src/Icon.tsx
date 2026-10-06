import type { HTMLAttributes } from "react";

type IconProps = HTMLAttributes<HTMLSpanElement> & {
  /** Material Symbols name, for example "close" or "search". Browse: https://fonts.google.com/icons */
  name: string;
  /** Accessible label. Omit for decorative icons. */
  label?: string;
};

/** Google Material Symbols (Outlined). The font loads from the `material-symbols` package. */
export function Icon({ name, label, className = "", ...rest }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      {...rest}
    >
      {name}
    </span>
  );
}
