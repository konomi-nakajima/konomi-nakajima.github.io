import os,re,glob,sys
from PIL import Image
S='/Users/konomi/Documents/portfolio-site/site'
skip={'og-image.jpg','favicon.png','webclip.png'}
before=after=0; n=0
for f in glob.glob(S+'/images/**/*.*',recursive=True):
    ext=os.path.splitext(f)[1].lower()
    if ext not in ('.png','.jpg','.jpeg') or os.path.basename(f) in skip: continue
    im=Image.open(f)
    is_photo = ext in ('.jpg','.jpeg')
    im=im.convert('RGBA' if im.mode in ('RGBA','LA','P') and 'transparency' in im.info or im.mode=='RGBA' else 'RGB')
    out=os.path.splitext(f)[0]+'.webp'
    if is_photo: im.save(out,'WEBP',quality=82,method=6)
    else:        im.save(out,'WEBP',quality=90,method=6)
    before+=os.path.getsize(f); after+=os.path.getsize(out); n+=1
    os.remove(f)
print(n,'images converted:',round(before/1e6,1),'MB ->',round(after/1e6,1),'MB')
# rewrite references
for h in glob.glob(S+'/**/*.html',recursive=True):
    t=open(h).read()
    t2=re.sub(r'(/images/(?:[\w-]+/)+[\w.-]+?)\.(?:png|jpe?g)(?=[\s"])',lambda m: m.group(0) if os.path.basename(m.group(0)) in skip else m.group(1)+'.webp',t)
    if t2!=t: open(h,'w').write(t2)
