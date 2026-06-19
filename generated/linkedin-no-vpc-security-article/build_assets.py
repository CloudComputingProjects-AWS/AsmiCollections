from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(__file__).resolve().parent

W, H = 1600, 900

PALETTE = {
    "ink": "#111827",
    "muted": "#4b5563",
    "blue": "#1d4ed8",
    "blue2": "#dbeafe",
    "green": "#15803d",
    "green2": "#dcfce7",
    "amber": "#b45309",
    "amber2": "#fef3c7",
    "red": "#b91c1c",
    "red2": "#fee2e2",
    "slate": "#334155",
    "slate2": "#f1f5f9",
    "white": "#ffffff",
    "line": "#94a3b8",
}

FONT_DIR = Path("C:/Windows/Fonts")


def font(name, size):
    for candidate in [name, "arial.ttf", "segoeui.ttf"]:
        p = FONT_DIR / candidate
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F_TITLE = font("arialbd.ttf", 54)
F_H1 = font("arialbd.ttf", 42)
F_H2 = font("arialbd.ttf", 31)
F_BODY = font("arial.ttf", 25)
F_SMALL = font("arial.ttf", 21)
F_BOLD = font("arialbd.ttf", 25)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_text(draw, xy, text, fnt, fill=PALETTE["ink"], max_w=None, gap=6):
    x, y = xy
    if max_w:
        lines = wrap(draw, text, fnt, max_w)
    else:
        lines = text.split("\n")
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += draw.textbbox((0, 0), line, font=fnt)[3] + gap
    return y


def card(draw, box, title, body, fill, stroke, title_color=None):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=22, fill=fill, outline=stroke, width=4)
    title_color = title_color or PALETTE["ink"]
    y = draw_text(draw, (x1 + 24, y1 + 20), title, F_H2, title_color, x2 - x1 - 48, 4)
    draw_text(draw, (x1 + 24, y + 10), body, F_BODY, PALETTE["muted"], x2 - x1 - 48, 5)


def arrow(draw, start, end, color=PALETTE["slate"], width=5):
    draw.line([start, end], fill=color, width=width)
    sx, sy = start
    ex, ey = end
    ang = math.atan2(ey - sy, ex - sx)
    size = 18
    pts = [
        (ex, ey),
        (ex - size * math.cos(ang - math.pi / 6), ey - size * math.sin(ang - math.pi / 6)),
        (ex - size * math.cos(ang + math.pi / 6), ey - size * math.sin(ang + math.pi / 6)),
    ]
    draw.polygon(pts, fill=color)


def header(img, title, subtitle):
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, H), fill="#f8fafc")
    draw.rectangle((0, 0, W, 140), fill="#0f172a")
    draw_text(draw, (60, 36), title, F_TITLE, PALETTE["white"], 1200)
    draw_text(draw, (62, 95), subtitle, F_BODY, "#cbd5e1", 1250)
    return draw


def hero():
    img = Image.new("RGB", (W, H), "#f8fafc")
    draw = header(
        img,
        "Securing E-Commerce Without VPC",
        "Cost-conscious serverless security using edge controls, signed callbacks, and app hardening",
    )

    card(draw, (70, 230, 420, 420), "Business Constraint", "Avoid VPC/NAT gateway complexity and recurring cost while keeping the public e-commerce API safe.", PALETTE["amber2"], PALETTE["amber"])
    card(draw, (610, 220, 990, 440), "Architecture Choice", "CloudFront + WAF + API Gateway + Lambda. No VPC attached to the backend Lambda.", PALETTE["blue2"], PALETTE["blue"])
    card(draw, (1180, 230, 1530, 420), "Security Outcome", "Layered controls moved to the edge, API layer, and application code.", PALETTE["green2"], PALETTE["green"])

    arrow(draw, (420, 325), (610, 325), PALETTE["slate"])
    arrow(draw, (990, 325), (1180, 325), PALETTE["slate"])

    bands = [
        ("CloudFront WAF", "bot and flood blocking", 150),
        ("API Gateway", "request throttling before Lambda", 390),
        ("FastAPI Lambda", "HMAC callbacks + security headers", 630),
        ("Data Layer", "SSL DB + PII encryption", 870),
        ("Secrets Plan", "dev env vars, production Secrets Manager + SSM", 1110),
    ]
    y = 560
    for title, body, x in bands:
        card(draw, (x, y, x + 210, y + 210), title, body, PALETTE["white"], PALETTE["line"])
    OUT.joinpath("01-hero-no-vpc-security.png").write_bytes(to_png(img))


def to_png(img):
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def risk_matrix():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(img, "Security Concerns Without VPC", "What was exposed, what could go wrong, and where the control now lives")
    rows = [
        ("Public API exposure", "Anyone on internet can send traffic", "API Gateway throttling + CloudFront WAF Block rule"),
        ("Image callback trust", "Fake 'image processed' message could update DB", "HMAC signature + timestamp replay protection"),
        ("Secrets in Lambda env", "Secrets visible to broad Lambda config access", "Dev accepted; production Secrets Manager + SSM"),
        ("API response headers", "Browser attacks such as clickjacking or MIME sniffing", "FastAPI app-level security headers"),
        ("Payment authenticity", "Forged payment status updates", "Payment webhook signature verification"),
    ]
    x = [70, 450, 870, 1180]
    y = 220
    headers = ["Concern", "Impact", "Implemented Control"]
    for i, h in enumerate(headers):
        draw.rounded_rectangle((x[i], y, x[i + 1] - 20 if i < 2 else 1530, y + 70), radius=14, fill="#0f172a")
        draw_text(draw, (x[i] + 18, y + 18), h, F_BOLD, PALETTE["white"])
    y += 92
    for concern, impact, control in rows:
        card(draw, (70, y, 430, y + 100), concern, "", PALETTE["slate2"], PALETTE["line"])
        draw_text(draw, (468, y + 28), impact, F_BODY, PALETTE["red"], 360)
        draw_text(draw, (890, y + 28), control, F_BODY, PALETTE["green"], 590)
        y += 120
    OUT.joinpath("02-risk-matrix.png").write_bytes(to_png(img))


def layered_controls():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(img, "No VPC: Security Moves to Layers", "Controls are placed before Lambda, inside Lambda, and at data/service boundaries")
    layers = [
        ("Internet Users and Bots", PALETTE["slate2"], PALETTE["slate"]),
        ("CloudFront WAF: Blocks IPs crossing rate threshold", PALETTE["red2"], PALETTE["red"]),
        ("API Gateway: Throttles bursts before Lambda cost", PALETTE["amber2"], PALETTE["amber"]),
        ("FastAPI Lambda: Auth, HMAC callback verification, security headers", PALETTE["blue2"], PALETTE["blue"]),
        ("Data & Integrations: SSL DB, encrypted PII, signed payment webhooks", PALETTE["green2"], PALETTE["green"]),
    ]
    y = 195
    for i, (title, fill, stroke) in enumerate(layers):
        x1 = 180 + i * 55
        x2 = 1420 - i * 55
        draw.rounded_rectangle((x1, y, x2, y + 92), radius=26, fill=fill, outline=stroke, width=5)
        draw_text(draw, (x1 + 35, y + 26), title, F_BOLD, PALETTE["ink"], x2 - x1 - 70)
        if i < len(layers) - 1:
            arrow(draw, ((x1 + x2) // 2, y + 92), ((x1 + x2) // 2, y + 126), PALETTE["line"], 4)
        y += 126
    OUT.joinpath("03-layered-controls.png").write_bytes(to_png(img))


def hmac_flow():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(img, "Image Callback: Secured Completion Message", "The processor must prove the completion message really came from our Lambda")
    nodes = [
        ((70, 250, 350, 455), "1. Raw Image", "Admin uploads product image to S3"),
        ((450, 230, 760, 485), "2. Image Lambda", "Creates WebP variants and prepares completion JSON"),
        ((860, 230, 1170, 485), "3. Backend Callback", "Checks HMAC signature and timestamp first"),
        ((1270, 250, 1530, 455), "4. Database", "Updates image URLs only after verification"),
    ]
    for box, title, body in nodes:
        card(draw, box, title, body, PALETTE["white"], PALETTE["blue"])
    arrow(draw, (350, 365), (450, 365))
    arrow(draw, (760, 365), (860, 365))
    arrow(draw, (1170, 365), (1270, 365))
    draw.rounded_rectangle((140, 585, 725, 765), radius=24, fill=PALETTE["red2"], outline=PALETTE["red"], width=3)
    draw_text(draw, (170, 615), "Old risk", F_H2, PALETTE["red"])
    draw_text(draw, (170, 670), "An attacker could post fake completion data if the endpoint URL was known.", F_BODY, PALETTE["ink"], 500)
    draw.rounded_rectangle((875, 585, 1460, 765), radius=24, fill=PALETTE["green2"], outline=PALETTE["green"], width=3)
    draw_text(draw, (905, 615), "New control", F_H2, PALETTE["green"])
    draw_text(draw, (905, 670), "Backend accepts only HMAC_SHA256(secret, timestamp + body) within a 5-minute window.", F_BODY, PALETTE["ink"], 500)
    OUT.joinpath("04-hmac-callback-flow.png").write_bytes(to_png(img))


def before_after():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(img, "Security Before vs After", "How the architecture compensated for not using VPC")
    card(draw, (90, 220, 725, 760), "Before", "Public Lambda/API\nUnauthenticated image callback\nRate limiting unclear from app code\nSecurity headers partial at edge\nSecrets directly in Lambda env", PALETTE["red2"], PALETTE["red"], PALETTE["red"])
    card(draw, (875, 220, 1510, 760), "After", "HMAC image callback\nAPI Gateway throttling verified\nCloudFront WAF Block mode verified\nFastAPI fallback security headers\nProduction secret-store plan", PALETTE["green2"], PALETTE["green"], PALETTE["green"])
    arrow(draw, (725, 490), (875, 490), PALETTE["slate"], 7)
    OUT.joinpath("05-before-after.png").write_bytes(to_png(img))


def no_vpc_decision_map():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(
        img,
        "No VPC Does Not Mean No Security",
        "We avoided VPC/NAT cost, then placed controls at the edge, API, app, and data layers",
    )

    card(draw, (80, 230, 430, 450), "Cost Decision", "Backend Lambda is not attached to a VPC to avoid extra network complexity and NAT gateway cost.", PALETTE["amber2"], PALETTE["amber"])
    card(draw, (625, 215, 975, 465), "Risk Created", "Public endpoints and service callbacks must be explicitly protected.", PALETTE["red2"], PALETTE["red"])
    card(draw, (1170, 230, 1520, 450), "Control Strategy", "Use managed AWS gates plus code-level cryptographic checks.", PALETTE["green2"], PALETTE["green"])
    arrow(draw, (430, 340), (625, 340), PALETTE["slate"])
    arrow(draw, (975, 340), (1170, 340), PALETTE["slate"])

    controls = [
        ("CloudFront WAF", "blocks abusive IPs"),
        ("API Gateway", "throttles request bursts"),
        ("FastAPI", "auth, HMAC callback, headers"),
        ("Database", "SSL and encrypted PII"),
    ]
    x = 140
    for title, body in controls:
        card(draw, (x, 590, x + 285, 775), title, body, PALETTE["white"], PALETTE["blue"])
        x += 360

    OUT.joinpath("06-no-vpc-decision-map.png").write_bytes(to_png(img))


def cloudfront_edge_security():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(
        img,
        "CloudFront: CDN plus Security Edge",
        "Customer traffic reaches AWS edge locations before it reaches API Gateway or Lambda",
    )

    benefits = [
        ("CDN Caching", "reduces origin load"),
        ("WAF at Edge", "blocks abusive traffic early"),
        ("TLS Front Door", "serves HTTPS to viewers at the edge"),
        ("DDoS Resiliency", "uses AWS edge capacity"),
        ("Header Policies", "can add security headers"),
    ]
    y = 190
    for title, body in benefits:
        card(draw, (70, y, 610, y + 122), title, body, PALETTE["slate2"], PALETTE["line"])
        y += 135

    draw.rounded_rectangle((780, 225, 1490, 720), radius=30, fill=PALETTE["blue2"], outline=PALETTE["blue"], width=5)
    draw_text(draw, (830, 265), "Our no-VPC request path", F_H1, PALETTE["ink"], 580)
    path = [
        ("1", "Browser / mobile client"),
        ("2", "CloudFront edge location"),
        ("3", "CloudFront WAF rate-based Block rule"),
        ("4", "API Gateway throttling"),
        ("5", "FastAPI backend Lambda"),
    ]
    sy = 355
    for number, label in path:
        draw.ellipse((835, sy, 885, sy + 50), fill=PALETTE["white"], outline=PALETTE["blue"], width=4)
        draw_text(draw, (852, sy + 10), number, F_BOLD, PALETTE["blue"])
        draw_text(draw, (915, sy + 10), label, F_BODY, PALETTE["ink"], 500)
        if number != "5":
            arrow(draw, (860, sy + 55), (860, sy + 83), PALETTE["line"], 3)
        sy += 78

    OUT.joinpath("09-cloudfront-edge-security.png").write_bytes(to_png(img))


def rate_limit_flow():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(
        img,
        "Public Traffic Control Without VPC",
        "Bad traffic is stopped before it becomes Lambda cost or customer impact",
    )

    nodes = [
        ((70, 285, 340, 470), "Internet", "Customers, bots, crawlers, broken clients"),
        ((430, 255, 725, 500), "CloudFront WAF", "Rate-based rule blocks abusive IPs at the edge"),
        ((820, 255, 1115, 500), "API Gateway", "Stage throttling limits burst and steady request rate"),
        ((1210, 285, 1530, 470), "Backend Lambda", "Receives traffic after managed gates"),
    ]
    for box, title, body in nodes:
        stroke = PALETTE["red"] if title == "CloudFront WAF" else PALETTE["blue"]
        fill = PALETTE["red2"] if title == "CloudFront WAF" else PALETTE["white"]
        card(draw, box, title, body, fill, stroke)
    arrow(draw, (340, 378), (430, 378))
    arrow(draw, (725, 378), (820, 378))
    arrow(draw, (1115, 378), (1210, 378))

    draw.rounded_rectangle((160, 620, 1440, 770), radius=26, fill=PALETTE["green2"], outline=PALETTE["green"], width=4)
    draw_text(draw, (200, 650), "Verified in AWS dev", F_H2, PALETTE["green"])
    draw_text(draw, (200, 705), "API Gateway: burst 100, rate 500.0   |   WAF: AWS-RateBasedRule-IP-1000-CreatedByCloudFront in Block mode", F_BODY, PALETTE["ink"], 1180)

    OUT.joinpath("07-rate-limiting-waf-flow.png").write_bytes(to_png(img))


def security_headers_map():
    img = Image.new("RGB", (W, H), PALETTE["white"])
    draw = header(
        img,
        "App-Level Security Headers",
        "Browser-facing protections are added by FastAPI, not left to guesswork",
    )

    headers = [
        ("X-Frame-Options", "DENY", "helps prevent clickjacking"),
        ("X-Content-Type-Options", "nosniff", "prevents MIME type guessing"),
        ("Referrer-Policy", "strict-origin-when-cross-origin", "limits URL data leakage"),
        ("Permissions-Policy", "camera=(), microphone=(), geolocation=()", "disables unused browser features"),
        ("Content-Security-Policy", "default-src 'none'", "restricts unsafe loading behavior"),
        ("Strict-Transport-Security", "enabled for HTTPS envs", "helps prevent HTTP downgrade"),
    ]

    y = 205
    for name, value, purpose in headers:
        draw.rounded_rectangle((90, y, 1510, y + 85), radius=18, fill=PALETTE["slate2"], outline=PALETTE["line"], width=3)
        draw_text(draw, (120, y + 18), name, F_BOLD, PALETTE["blue"], 360)
        draw_text(draw, (520, y + 18), value, F_SMALL, PALETTE["ink"], 420)
        draw_text(draw, (980, y + 18), purpose, F_SMALL, PALETTE["green"], 470)
        y += 100

    OUT.joinpath("08-security-headers-map.png").write_bytes(to_png(img))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    hero()
    risk_matrix()
    layered_controls()
    hmac_flow()
    before_after()
    no_vpc_decision_map()
    cloudfront_edge_security()
    rate_limit_flow()
    security_headers_map()
    print(OUT)
