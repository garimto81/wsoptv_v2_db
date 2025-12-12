import { test, expect } from '@playwright/test'

test.describe('Catalog Validation Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/catalog/validation')
  })

  test('should load validation page', async ({ page }) => {
    await expect(page).toHaveTitle(/PokerVOD|Catalog/)
    await expect(page.getByRole('heading', { name: /Catalog Validation/i })).toBeVisible()
  })

  test('should display summary cards', async ({ page }) => {
    // Total Items card
    await expect(page.getByText('Total Items')).toBeVisible()

    // Title Coverage card
    await expect(page.getByText('Title Coverage')).toBeVisible()

    // Projects card
    await expect(page.getByText('Projects')).toBeVisible()

    // Quality Score card
    await expect(page.getByText('Quality Score')).toBeVisible()
  })

  test('should have tabs for different views', async ({ page }) => {
    await expect(page.getByRole('tab', { name: /프로젝트별/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /파서별 샘플/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /연도별/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /품질 이슈/i })).toBeVisible()
  })

  test('should switch between tabs', async ({ page }) => {
    // Click on parser samples tab
    await page.getByRole('tab', { name: /파서별 샘플/i }).click()
    // Check tab is active
    await expect(page.getByRole('tab', { name: /파서별 샘플/i })).toHaveAttribute('data-state', 'active')

    // Click on year tab
    await page.getByRole('tab', { name: /연도별/i }).click()
    await expect(page.getByRole('tab', { name: /연도별/i })).toHaveAttribute('data-state', 'active')

    // Click on issues tab
    await page.getByRole('tab', { name: /품질 이슈/i }).click()
    await expect(page.getByRole('tab', { name: /품질 이슈/i })).toHaveAttribute('data-state', 'active')
  })

  test('should load data from API', async ({ page }) => {
    // Wait for API response and check data is displayed
    await page.waitForResponse(
      (response) =>
        response.url().includes('/quality/catalog/summary') &&
        response.status() === 200
    )

    // Should show actual numbers, not loading state
    const totalItems = page.locator('text=/\\d+/')
    await expect(totalItems.first()).toBeVisible()
  })

  test('should display project distribution', async ({ page }) => {
    // Should show project codes like WSOP
    await expect(page.getByText('WSOP')).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Catalog Validation API', () => {
  test('summary API returns valid data', async ({ request }) => {
    const response = await request.get(
      'http://localhost:8004/api/v1/quality/catalog/summary'
    )
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    expect(data.total_items).toBeGreaterThan(0)
    expect(data.title_coverage_rate).toBeGreaterThanOrEqual(0)
    expect(Array.isArray(data.by_project)).toBeTruthy()
  })

  test('samples API returns valid data', async ({ request }) => {
    const response = await request.get(
      'http://localhost:8004/api/v1/quality/catalog/samples'
    )
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    expect(Array.isArray(data)).toBeTruthy()
  })

  test('title quality API returns valid data', async ({ request }) => {
    const response = await request.get(
      'http://localhost:8004/api/v1/quality/catalog/titles/quality'
    )
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    expect(data.total_analyzed).toBeGreaterThanOrEqual(0)
    expect(data.quality_score).toBeGreaterThanOrEqual(0)
  })
})
