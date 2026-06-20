$ErrorActionPreference = "Stop"

$outputDir = Join-Path (Get-Location) ".firecrawl\marketlens_sources"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$queries = @(
  "瑞幸咖啡 Luckin Coffee 价格促销 门店密度 2025 2026",
  "库迪咖啡 Cotti Coffee 价格战 扩张 中国 2025 2026",
  "星巴克中国 Starbucks China 战略 门店扩张 2025 2026",
  "蜜雪冰城 Mixue 招股书 加盟 门店扩张",
  "霸王茶姬 CHAGEE 招股书 高端茶饮 扩张 2025 2026",
  "古茗 Guming 招股书 茶饮 加盟 扩张",
  "茶百道 ChaPanda 招股书 茶饮 加盟 扩张",
  "China fresh beverage tea coffee market price war 2025 2026"
)

function ConvertTo-Slug {
  param([Parameter(Mandatory = $true)][string]$Text)

  $slug = $Text.ToLowerInvariant() -replace "[^a-z0-9]+", "-"
  return $slug.Trim("-")
}

foreach ($query in $queries) {
  $slug = ConvertTo-Slug -Text $query
  $target = Join-Path $outputDir "$slug.json"

  Write-Host "Searching: $query"
  $json = & firecrawl search $query --limit 5 --format json
  if ($LASTEXITCODE -ne 0) {
    throw "firecrawl search failed for query: $query"
  }

  $json | Set-Content -Path $target -Encoding utf8
}
