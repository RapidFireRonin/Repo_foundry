import { expect, test } from "@playwright/test";

test("Chrono Rift proves future knowledge unlocks the safer past solution and chapter ending", async ({ page }) => {
  await page.goto("/chrono-rift.html");

  await expect(page.getByRole("heading", { name: "Chrono Rift: Echoes of the Broken Hour" })).toBeVisible();
  await expect(page.getByText("Critical time-travel proof path")).toBeVisible();

  await page.getByRole("button", { name: "Search the rubble" }).click();
  await page.getByRole("button", { name: "Force open the tower gate" }).click();
  await page.getByRole("button", { name: "Future" }).click();
  await page.getByRole("button", { name: "Read the monument inscription" }).click();
  await expect(page.getByText("✓ Jump to the Future and read the monument inscription.")).toBeVisible();

  await page.getByRole("button", { name: "Study the survivor mural" }).click();
  await page.getByRole("button", { name: "Salvage a chronal fuse" }).click();
  await page.getByRole("button", { name: "Past" }).click();
  await page.getByRole("button", { name: "Sabotage the Guild crate quietly" }).click();
  await expect(page.getByText("✓ Jump to the Past and use the future clue to safely discharge the Guild crate.")).toBeVisible();

  await page.getByRole("button", { name: "Buy the blue lantern from a nervous courier" }).click();
  await page.getByRole("button", { name: "Present" }).click();
  await page.getByRole("button", { name: "Force open the tower gate" }).click();
  await page.getByRole("button", { name: "Install the Blue Lantern blindly" }).click();
  await page.getByRole("button", { name: "Fit the Chronal Fuse" }).click();
  await page.getByRole("button", { name: "Confront Vale with the hidden truth" }).click();
  await page.getByRole("button", { name: "Seal the rift" }).click();

  await expect(page.getByText("Chapter Complete")).toBeVisible();
  await expect(page.getByText("Verified: the chapter ending required knowledge from the future, a changed past, and present repair choices.")).toBeVisible();
});
