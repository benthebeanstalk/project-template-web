import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Icon } from "./Icon";

test("labeled icon is exposed as an image with its name as the glyph", () => {
  render(<Icon name="close" label="Remove" />);
  const icon = screen.getByRole("img", { name: "Remove" });
  expect(icon).toHaveClass("material-symbols-outlined");
  expect(icon).toHaveTextContent("close");
});

test("unlabeled icon is hidden from assistive technology", () => {
  const { container } = render(<Icon name="search" />);
  expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
  expect(screen.queryByRole("img")).toBeNull();
});
