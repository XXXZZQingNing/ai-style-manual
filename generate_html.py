import os
import urllib.parse
from PIL import Image
import shutil

def generate_html(output_filename="index.html"):
    root_dir = "."
    thumb_dir = "thumbnails"
    
    # Create thumbnails directory if it doesn't exist
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)

    # Get all subdirectories (categories)
    # Exclude thumbnails dir and hidden dirs
    categories = [d for d in os.listdir(root_dir) 
                 if os.path.isdir(os.path.join(root_dir, d)) 
                 and not d.startswith('.') 
                 and d != thumb_dir]
    categories.sort()

    # Collect data and generate thumbnails
    gallery_data = {}
    
    print("正在扫描图片并生成缩略图 (这可能需要一点时间)...")
    
    for category in categories:
        category_path = os.path.join(root_dir, category)
        category_thumb_path = os.path.join(thumb_dir, category)
        
        if not os.path.exists(category_thumb_path):
            os.makedirs(category_thumb_path)
            
        images = []
        for f in os.listdir(category_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')):
                images.append(f)
        
        images.sort()
        if images:
            gallery_data[category] = images
            
            # Generate thumbnails for this category
            for img_file in images:
                src_path = os.path.join(category_path, img_file)
                thumb_path = os.path.join(category_thumb_path, img_file)
                
                # Check if thumbnail already exists to save time
                if not os.path.exists(thumb_path):
                    try:
                        with Image.open(src_path) as img:
                            # Convert to RGB if necessary (e.g. for RGBA pngs saving as JPEG, though we keep extension)
                            if img.mode in ('RGBA', 'LA') and False: 
                                # Actually let's keep original format if possible, or convert to RGB for compatibility
                                # WebP handles RGBA.
                                pass
                                
                            # Resize: Max 400px width/height
                            img.thumbnail((400, 400))
                            img.save(thumb_path, quality=80)
                            # print(f"Generated thumbnail: {thumb_path}")
                    except Exception as e:
                        print(f"Error processing {src_path}: {e}")
                
    print("缩略图生成完成。正在生成 HTML...")

    # HTML Template parts
    html_head = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 风格手册图片集</title>
    <style>
        :root {
            --bg-color: #121212;
            --sidebar-bg: #1e1e1e;
            --card-bg: #252525;
            --text-main: #e0e0e0;
            --text-muted: #aaaaaa;
            --accent-color: #3498db;
            --sidebar-width: 260px;
            --header-height: 60px;
        }

        * {
            box-sizing: border_box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* --- Sidebar Navigation --- */
        .sidebar {
            height: 100vh;
            width: var(--sidebar-width);
            position: fixed;
            top: 0;
            left: 0;
            background-color: var(--sidebar-bg);
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 2px 0 10px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
        }

        .sidebar-header {
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid #333;
            background-color: var(--sidebar-bg);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .sidebar-header h2 {
            font-size: 1.2rem;
            color: #fff;
            letter-spacing: 1px;
        }

        .nav-links {
            padding: 10px 0;
        }

        .nav-links a {
            padding: 12px 25px;
            text-decoration: none;
            font-size: 0.95rem;
            color: var(--text-muted);
            display: block;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }

        .nav-links a:hover, .nav-links a.active {
            color: #fff;
            background-color: rgba(255,255,255,0.05);
            border-left-color: var(--accent-color);
        }

        /* --- Mobile Header --- */
        .mobile-header {
            display: none; /* Hidden on desktop */
            height: var(--header-height);
            background-color: var(--sidebar-bg);
            align-items: center;
            padding: 0 20px;
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 999;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        .menu-toggle {
            font-size: 24px;
            cursor: pointer;
            color: #fff;
            margin-right: 15px;
        }

        .mobile-title {
            font-size: 1.1rem;
            font-weight: bold;
        }

        /* --- Main Content --- */
        .main {
            margin-left: var(--sidebar-width);
            padding: 40px;
            transition: margin-left 0.3s ease;
            min-height: 100vh;
        }

        h1.page-title {
            font-size: 2rem;
            margin-bottom: 30px;
            color: #fff;
            display: none; /* Hide main title on mobile if redundant */
        }
        
        @media (min-width: 769px) {
            h1.page-title { display: block; }
        }

        .category-section {
            margin-bottom: 50px;
            scroll-margin-top: 20px; /* For anchor positioning */
        }
        
        /* Adjust scroll position for fixed header on mobile */
        @media (max-width: 768px) {
            .category-section {
                scroll-margin-top: calc(var(--header-height) + 20px);
            }
        }

        .category-title {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: var(--accent-color);
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }

        /* --- Grid Layout --- */
        .gallery-grid {
            display: grid;
            /* Adaptive columns: min 160px wide */
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 15px;
        }

        .image-card {
            background-color: var(--card-bg);
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
        }

        .image-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.4);
            z-index: 2;
        }

        .image-container {
            width: 100%;
            padding-top: 100%; /* 1:1 Aspect Ratio Square */
            position: relative;
            background-color: #2a2a2a;
        }

        .image-card img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover; /* Crop to fill square */
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .image-card img.loaded {
            opacity: 1;
        }

        .image-info {
            padding: 10px;
            font-size: 0.85rem;
            color: #ccc;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* --- Lightbox --- */
        .lightbox {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.95);
            justify-content: center;
            align-items: center;
            flex-direction: column;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .lightbox.show {
            opacity: 1;
        }

        .lightbox-content {
            max-width: 95%;
            max-height: 85vh;
            object-fit: contain;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
            border-radius: 4px;
        }

        .lightbox-caption {
            margin-top: 15px;
            color: #fff;
            font-size: 1.1rem;
            text-align: center;
        }
        
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 30px;
            color: #fff;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
            z-index: 2001;
        }
        
        /* --- Responsive Queries --- */
        @media (max-width: 768px) {
            .mobile-header {
                display: flex;
            }

            .sidebar {
                transform: translateX(-100%); /* Hide sidebar by default */
                width: 250px;
                padding-top: var(--header-height); /* Make room for header inside if needed, or just overlay */
                top: 0; /* Below header? Or full height overlay? Let's do full height overlay */
                padding-top: 0;
            }
            
            .sidebar.active {
                transform: translateX(0);
            }
            
            /* Overlay when sidebar is open */
            .sidebar-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 999;
                opacity: 0;
                transition: opacity 0.3s;
            }
            
            .sidebar-overlay.active {
                display: block;
                opacity: 1;
            }

            .main {
                margin-left: 0;
                padding: 20px;
                padding-top: calc(var(--header-height) + 20px);
            }

            .gallery-grid {
                /* 2 columns on mobile usually looks best */
                grid-template-columns: repeat(2, 1fr); 
                gap: 10px;
            }
            
            .image-info {
                font-size: 0.75rem;
                padding: 8px 5px;
            }
        }
    </style>
</head>
<body>

<!-- Mobile Header -->
<div class="mobile-header">
    <div class="menu-toggle" onclick="toggleSidebar()">☰</div>
    <div class="mobile-title">AI 风格手册</div>
</div>

<!-- Sidebar Overlay -->
<div class="sidebar-overlay" onclick="toggleSidebar()"></div>

<!-- Sidebar -->
<div class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <h2>分类导航</h2>
    </div>
    <div class="nav-links">
"""

    html_nav = ""
    for category in gallery_data.keys():
        html_nav += f'        <a href="#{category}" onclick="closeSidebarOnMobile()">{category}</a>\n'

    html_mid = """
    </div>
</div>

<div class="main">
    <h1 class="page-title">AI 风格手册图片集</h1>
"""

    html_content = ""
    for category, images in gallery_data.items():
        html_content += f"""
    <div id="{category}" class="category-section">
        <h2 class="category-title">{category}</h2>
        <div class="gallery-grid">
"""
        for img_file in images:
            # Paths
            # Thumbnails for the grid
            thumb_path = f"{thumb_dir}/{category}/{img_file}"
            thumb_url = urllib.parse.quote(thumb_path)
            
            # Original for the lightbox
            original_path = f"{category}/{img_file}"
            original_url = urllib.parse.quote(original_path)
            
            img_name = os.path.splitext(img_file)[0]
            
            # Use data-src for lazy loading implementation if we wanted custom JS, 
            # but native loading="lazy" is good. 
            # We use onload="this.classList.add('loaded')" for fade-in effect.
            
            html_content += f"""
            <div class="image-card" onclick="openLightbox('{original_url}', '{img_name}')">
                <div class="image-container">
                    <img src="{thumb_url}" alt="{img_name}" loading="lazy" onload="this.classList.add('loaded')">
                </div>
                <div class="image-info">
                    <div class="image-name">{img_name}</div>
                </div>
            </div>
"""
        html_content += """
        </div>
    </div>
"""

    html_footer = """
</div>

<!-- Lightbox Modal -->
<div id="myLightbox" class="lightbox" onclick="if(event.target === this) closeLightbox()">
  <span class="lightbox-close" onclick="closeLightbox()">&times;</span>
  <img class="lightbox-content" id="lightbox-img">
  <div id="lightbox-caption" class="lightbox-caption"></div>
</div>

<script>
    // Sidebar Toggle for Mobile
    function toggleSidebar() {
        document.getElementById('sidebar').classList.toggle('active');
        document.querySelector('.sidebar-overlay').classList.toggle('active');
    }

    function closeSidebarOnMobile() {
        if (window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.remove('active');
            document.querySelector('.sidebar-overlay').classList.remove('active');
        }
    }

    // Lightbox
    const lightbox = document.getElementById("myLightbox");
    const lightboxImg = document.getElementById("lightbox-img");
    const lightboxCaption = document.getElementById("lightbox-caption");

    function openLightbox(src, alt) {
        lightbox.style.display = "flex";
        // Small delay to allow display:flex to apply before opacity transition
        setTimeout(() => {
            lightbox.classList.add("show");
        }, 10);
        
        lightboxImg.src = src;
        lightboxCaption.textContent = alt;
        document.body.style.overflow = "hidden"; // Prevent background scrolling
    }

    function closeLightbox() {
        lightbox.classList.remove("show");
        setTimeout(() => {
            lightbox.style.display = "none";
            lightboxImg.src = ""; // Clear src to stop memory usage
        }, 300);
        document.body.style.overflow = "";
    }

    // Keyboard support
    document.addEventListener('keydown', function(event) {
        if (event.key === "Escape") {
            closeLightbox();
        }
    });
</script>

</body>
</html>
"""

    full_html = html_head + html_nav + html_mid + html_content + html_footer

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print(f"HTML generated successfully: {output_filename}")

if __name__ == "__main__":
    generate_html()
