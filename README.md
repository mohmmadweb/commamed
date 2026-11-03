# commamed.com

Static website for **Comma Med (کامامد)**: an AI second-reader for mammography, by Sharif Future Electronic Health Company.

- Live: https://commamed.com
- Hosting: GitHub Pages (branch `main`, root). The custom domain is set in `CNAME`.
- No build step. Edit `index.html` and push. The site is updated in about a minute.

## Structure
| Path | Content |
|---|---|
| `index.html` | The whole page (Persian/English toggle, inline CSS and JS) |
| `img/` | Screenshots and charts |
| `logos/` | Partner and site logos |
| `fonts/` | Vazirmatn (OFL) |
| `og.jpg` | Social share image (1200×630) |

## Local preview
```bash
python3 -m http.server 8000
```

## DNS (Cloudflare)
DNS is kept as code in `dns/records.json`. Change that file and push to `main`: the **DNS (Cloudflare)** workflow applies it.
To only see the plan, run the workflow by hand from the Actions tab and leave `apply` unticked.

- Required repository secret: `CLOUDFLARE_API_TOKEN` (Zone → DNS → Edit and Zone → Zone → Read, limited to commamed.com).
- Only the names in the file are managed, and only their A/AAAA/CNAME records. MX, TXT and any name not listed are never touched.
- Everything is DNS only (grey cloud). `commamed.com` and `www` point to GitHub Pages. The service subdomains point to the Sharif server, which Cloudflare's proxy cannot reach.
