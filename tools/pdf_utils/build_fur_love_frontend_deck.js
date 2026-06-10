const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const out = path.join(root, "docs", "fur-love-india-launch-strategy-frontend.html");
const viewportCss = fs.readFileSync(
  "C:/Users/Devan/.codex/skills/frontend-slides/viewport-base.css",
  "utf8"
);

function asset(file, mime) {
  const p = path.join(root, file);
  return `data:${mime};base64,${fs.readFileSync(p).toString("base64")}`;
}

const img = {
  brandBlack: asset("docs/fur-love-wordmark-corrected.png", "image/png"),
  brandWhite: asset("docs/fur-love-assets/fur-love-wordmark-white.png", "image/png"),
  verveBlack: asset("docs/fur-love-assets/verve-media-black-deck.png", "image/png"),
  verveWhite: asset("docs/fur-love-assets/verve-media-white-deck.png", "image/png"),
  dogHero: asset("docs/fur-love-assets/pdf/intro-images/intro-p01-img01.jpeg", "image/jpeg"),
  userGolden: asset("docs/fur-love-assets/user-dog-golden.jpg", "image/jpeg"),
  userCloseup: asset("docs/fur-love-assets/user-dog-closeup.jpg", "image/jpeg"),
  userYorkie: asset("docs/fur-love-assets/user-dog-yorkie.jpg", "image/jpeg"),
  dogTowelBrand: asset("docs/fur-love-assets/pdf/intro-images/intro-p04-img02.jpeg", "image/jpeg"),
  dogHusky: asset("docs/fur-love-assets/pdf/intro-images/intro-p04-img06.jpeg", "image/jpeg"),
  dogCutout: asset("docs/fur-love-assets/pdf/concept-images/concept-p16-img01.png", "image/png"),
  productRange: asset("docs/fur-love-assets/pdf/intro-images/intro-p06-img01.jpeg", "image/jpeg"),
  productFlatlay: asset("docs/fur-love-assets/pdf/intro-images/intro-p07-img01.jpeg", "image/jpeg"),
  productPlate: asset("docs/fur-love-assets/pdf/intro-images/intro-p05-img01.jpeg", "image/jpeg"),
  balmHand: asset("docs/fur-love-assets/pdf/intro-images/intro-p03-img04.jpeg", "image/jpeg"),
  productFur: asset("docs/fur-love-assets/pdf/intro-images/intro-p03-img05.jpeg", "image/jpeg"),
  shampooBottle: asset("docs/fur-love-assets/pdf/intro-images/intro-p03-img02.jpeg", "image/jpeg"),
};

const slides = [
  `
  <section class="slide hero dark" data-theme="dark">
    <div class="photo fill hero-dog" style="--img:url('${img.userGolden}')"></div>
    <div class="wash dark-wash"></div>
    <header class="brand-row">
      <img class="brand-logo" src="${img.brandWhite}" alt="Fur Love">
      <img class="agency-logo" src="${img.verveWhite}" alt="Verve Media">
    </header>
    <div class="slide-content hero-copy">
      <p class="eyebrow reveal">India launch strategy</p>
      <h1 class="reveal">Fur Love,<br><em>For Love</em></h1>
      <p class="dek reveal">A social media launch that treats pet care like beauty care.</p>
    </div>
  </section>`,
  `
  <section class="slide editorial">
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content split">
      <div class="copy-pane">
        <p class="phase reveal">01 / The Gap</p>
        <h2 class="reveal">The love is premium. The category still looks basic.</h2>
        <p class="reveal">The emotional standard is premium. The visual standard is still functional, cute, clinical or pet-shop basic.</p>
      </div>
      <div class="gap-stack">
        <article class="gap-card reveal"><b>What the market shows</b><span>Safety, gentleness, hygiene and utility.</span></article>
        <article class="gap-card reveal"><b>What the audience feels</b><span>My dog deserves care that looks as considered as mine.</span></article>
        <article class="gap-card reveal"><b>Where Fur Love enters</b><span>Premium pet care that feels like a beauty ritual, not a chore.</span></article>
      </div>
    </div>
  </section>`,
  `
  <section class="slide image-left">
    <div class="photo side" style="--img:url('${img.productRange}')"></div>
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content right-copy">
      <p class="phase reveal">02 / Objective</p>
      <h2 class="reveal">Make dog care feel like beauty care.</h2>
      <p class="reveal">Texture, packaging, touch, ritual and final coat finish become the launch language.</p>
    </div>
  </section>`,
  `
  <section class="slide triptych">
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content">
      <p class="phase reveal">03 / Opportunity</p>
      <h2 class="reveal">The launch needs three signals.</h2>
      <div class="three-words">
        <article class="word-card reveal"><h3>Desire</h3><p>Make the product feel worth looking at before explaining everything.</p></article>
        <article class="word-card reveal"><h3>Ritual</h3><p>Show care as touch, texture, routine, coat finish and time spent together.</p></article>
        <article class="word-card reveal"><h3>Proof</h3><p>Use real dogs, real use and product behaviour to make the premium feel believable.</p></article>
      </div>
    </div>
  </section>`,
  `
  <section class="slide line-build dark" data-theme="dark">
    <div class="photo fill soft" style="--img:url('${img.balmHand}')"></div>
    <div class="wash dark-wash"></div>
    <header class="brand-row"><img class="brand-logo" src="${img.brandWhite}" alt="Fur Love"><img class="agency-logo" src="${img.verveWhite}" alt="Verve Media"></header>
    <div class="slide-content center-copy">
      <h2 class="massive reveal">FUR LOVE,</h2>
    </div>
  </section>`,
  `
  <section class="slide line-build cream">
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content center-copy">
      <h2 class="massive reveal"><span>FUR LOVE,</span><br><em>FOR LOVE</em></h2>
    </div>
  </section>`,
  `
  <section class="slide line-build meaning">
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content center-copy meaning-center">
      <p class="phase reveal">Communication thought</p>
      <h2 class="reveal">FUR LOVE,<br><em>FOR LOVE</em></h2>
      <div class="meaning-copy reveal">
        <p>Not a line about grooming. A line about the standard of care love deserves.</p>
      </div>
    </div>
  </section>`,
  `
  <section class="slide flow">
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content">
      <p class="phase reveal">04 / How It Moves</p>
      <h2 class="reveal">A luxury reveal, not a product catalogue.</h2>
      <div class="flow-line">
        <div class="step reveal"><b>01</b><span>Create desire</span><p>Make the product worth noticing before the feed explains it.</p></div>
        <div class="step reveal"><b>02</b><span>Show the gap</span><p>Make regular grooming feel visually basic without attacking it.</p></div>
        <div class="step reveal"><b>03</b><span>Reveal ritual</span><p>Move from touch and texture to product role and range.</p></div>
        <div class="step reveal"><b>04</b><span>Build recall</span><p>Repeat the same visual cues until Fur Love feels familiar.</p></div>
      </div>
    </div>
  </section>`,
  `
  <section class="slide phase-one">
    <div class="photo fill pale" style="--img:url('${img.productFlatlay}')"></div>
    <div class="wash cream-wash"></div>
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content phase-grid">
      <div>
        <p class="phase reveal">Phase 1 / Pre-launch</p>
        <h2 class="reveal">Build sightings before explanation.</h2>
        <p class="reveal">The audience should see fragments of the Fur Love world before they are asked to understand the full range.</p>
      </div>
      <div class="tile-grid">
        <div class="tile reveal"><b>Packaging crops</b><span>Cap, label, bottle edge, pouch colour, logo and product family details.</span></div>
        <div class="tile reveal"><b>Texture videos</b><span>Balm scoop, oil drop, shampoo pour, lather behaviour and product in hand.</span></div>
        <div class="tile reveal"><b>Beauty shelfies</b><span>Product placed like skincare: towel, stone, ceramic, brush, glass, sink.</span></div>
        <div class="tile reveal"><b>Ritual fragments</b><span>Hand on fur, towel wrap, paw hold, brush-through and soft finish.</span></div>
      </div>
    </div>
  </section>`,
  `
  <section class="slide takeover dark" data-theme="dark">
    <div class="photo fill" style="--img:url('${img.productPlate}')"></div>
    <div class="wash dark-wash"></div>
    <header class="brand-row"><img class="brand-logo" src="${img.brandWhite}" alt="Fur Love"><img class="agency-logo" src="${img.verveWhite}" alt="Verve Media"></header>
    <div class="slide-content takeover-layout">
      <div class="takeover-copy">
        <p class="phase reveal">Grand Pre-launch Activity</p>
        <h2 class="reveal">The Fur Love Takeover</h2>
        <p class="reveal">Outdoor + social teasers that look like beauty advertising, not pet advertising.</p>
      </div>
      <div class="billboard reveal">
        <img src="${img.brandBlack}" alt="Fur Love">
        <h3>Fur Love,<br><em>For Love</em></h3>
        <p>Coming soon to loved dogs.</p>
      </div>
    </div>
  </section>`,
  `
  <section class="slide launch dark" data-theme="dark">
    <div class="photo fill" style="--img:url('${img.userCloseup}')"></div>
    <div class="wash dark-wash"></div>
    <header class="brand-row"><img class="brand-logo" src="${img.brandWhite}" alt="Fur Love"><img class="agency-logo" src="${img.verveWhite}" alt="Verve Media"></header>
    <div class="slide-content right-copy light">
      <p class="phase reveal">Phase 2 / Launch</p>
      <h2 class="reveal">Reveal the ritual. Then the range.</h2>
      <p class="reveal">Hero film, launch reel, SKU demos, product range carousel and creator first-use cuts.</p>
    </div>
  </section>`,
  `
  <section class="slide awareness">
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content">
      <p class="phase reveal">Post-launch Awareness</p>
      <h2 class="reveal">Turn the launch into repeated recognition.</h2>
      <p class="reveal">Top of funnel here means making people remember the Fur Love world before asking them to shop: the look, the line, the ritual and the product behaviour.</p>
      <div class="media-grid">
        <div class="media reveal"><b>6s hooks</b><span>Texture, dog reaction, line, logo.</span></div>
        <div class="media reveal"><b>15s paid cuts</b><span>One problem, one ritual, one product role.</span></div>
        <div class="media reveal"><b>Creator cuts</b><span>First-use routines with premium homes and real dogs.</span></div>
        <div class="media reveal"><b>OOH recaps</b><span>Turn sightings into social proof and curiosity.</span></div>
        <div class="media reveal"><b>Packaging recall</b><span>Repeat the visual codes: label, colour, cap, shelf.</span></div>
        <div class="media reveal"><b>Education</b><span>No-bubble logic, texture logic, ingredient logic.</span></div>
      </div>
    </div>
  </section>`,
  `
  <section class="slide sustain">
    <div class="photo side right" style="--img:url('${img.userYorkie}')"></div>
    <header class="brand-row"><img class="brand-logo" src="${img.brandBlack}" alt="Fur Love"><img class="agency-logo" src="${img.verveBlack}" alt="Verve Media"></header>
    <div class="slide-content left-copy">
      <p class="phase reveal">Phase 3 / Sustainance</p>
      <h2 class="reveal">Sustain with four repeatable series.</h2>
      <div class="sustain-list reveal">
        <span>The Fur Love Ritual</span>
        <span>Beauty for Dogs</span>
        <span>Why We Do / Do Not Do This</span>
        <span>Real Parent Proof</span>
      </div>
    </div>
  </section>`,
  `
  <section class="slide final dark" data-theme="dark">
    <div class="photo fill soft hero-dog" style="--img:url('${img.userGolden}')"></div>
    <div class="wash dark-wash"></div>
    <header class="brand-row"><img class="brand-logo" src="${img.brandWhite}" alt="Fur Love"><img class="agency-logo" src="${img.verveWhite}" alt="Verve Media"></header>
    <div class="slide-content center-copy">
      <p class="phase reveal">Takeaway</p>
      <h2 class="reveal">Fur Love is the premium care brand for loved dogs.</h2>
      <p class="reveal">A beauty launch built around love, ritual and proof.</p>
    </div>
  </section>`,
];

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fur Love India Launch Strategy</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700&family=Cormorant+Garamond:ital,wght@1,500;1,600&family=Inter:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    /* === FUR LOVE DESIGN TOKENS === */
    :root {
      --paper:#FAF8F4; --cream:#F6F1E8; --oat:#EFE7D7; --stone:#E6DECB;
      --ink:#161514; --ink-2:#3C3935; --muted:#6B6660; --line:#D9D3CA;
      --lilac:#B8A3D6; --lilac-dark:#7A5BA8; --lilac-soft:#EADEF3;
      --petal:#E8C8C2; --sage:#A8B398; --clinical:#2F4A4A;
      --display:'Bricolage Grotesque', sans-serif;
      --body:'Inter', sans-serif;
      --serif:'Cormorant Garamond', serif;
      --title-size:clamp(2.4rem, 7.4vw, 7rem);
      --h2-size:clamp(2rem, 5.8vw, 5.6rem);
      --h3-size:clamp(1.2rem, 2.8vw, 2.4rem);
      --body-size:clamp(.9rem, 1.35vw, 1.32rem);
      --small-size:clamp(.72rem, 1vw, .95rem);
      --slide-padding:clamp(1.1rem, 4.4vw, 4.8rem);
      --content-gap:clamp(.8rem, 2vw, 2rem);
      --ease:cubic-bezier(.16,1,.3,1);
    }

    /* === MANDATORY VIEWPORT BASE === */
${viewportCss}

    /* === RESET AND GLOBAL SLIDE SYSTEM === */
    *{box-sizing:border-box} body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--body)}
    .slide{isolation:isolate;background:var(--cream)}
    .slide-content{z-index:3}
    .brand-row{position:absolute;top:clamp(1rem,2vw,1.65rem);left:clamp(1rem,3vw,3rem);right:clamp(1rem,3vw,3rem);display:flex;justify-content:space-between;align-items:flex-start;z-index:5}
    .brand-logo{width:clamp(7rem,11vw,10rem);height:auto;max-height:none;object-fit:contain}
    .agency-logo{width:clamp(5.8rem,8.4vw,8rem);height:auto;max-height:none;object-fit:contain}
    .photo{background-image:var(--img);background-size:cover;background-position:center;z-index:0}
    .photo.fill{position:absolute;inset:0}
    .photo.hero-dog{background-position:center 42%}
    .photo.side{position:absolute;left:0;top:0;width:50vw;height:100%;background-position:center}
    .photo.side.right{left:auto;right:0}
    .photo.soft{filter:saturate(.92) contrast(.96)}
    .photo.pale{filter:saturate(.86) contrast(.92) brightness(1.04)}
    .wash{position:absolute;inset:0;z-index:1;pointer-events:none}
    .dark-wash{background:linear-gradient(90deg,rgba(22,21,20,.86),rgba(22,21,20,.54) 45%,rgba(22,21,20,.2))}
    .cream-wash{background:linear-gradient(90deg,rgba(246,241,232,.98),rgba(246,241,232,.78) 52%,rgba(246,241,232,.18))}
    .eyebrow,.phase{font-family:var(--body);font-size:clamp(1rem,1.55vw,1.55rem);font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--lilac-dark);margin:0 0 clamp(.8rem,2vh,1.3rem)}
    .dark .phase,.dark .eyebrow{color:var(--petal)}
    h1,h2,h3,p{margin:0}
    h1,h2,h3{font-family:var(--display);font-weight:700;letter-spacing:0;line-height:.95;text-wrap:balance}
    h1{font-size:var(--title-size);max-width:10ch}
    h2{font-size:var(--h2-size);max-width:11ch}
    h3{font-size:var(--h3-size)}
    em{font-family:var(--serif);font-weight:600;color:var(--lilac)}
    p{font-size:var(--body-size);line-height:1.34;color:var(--ink-2);max-width:42ch}
    .dark h1,.dark h2,.dark h3,.dark p,.light h2,.light p{color:var(--paper)}
    .dark em{color:var(--petal)}
    .dek{font-size:clamp(1.05rem,1.8vw,1.7rem);max-width:31ch;color:var(--line)}

    /* === ANIMATIONS === */
    .reveal{opacity:0;transform:translateY(clamp(1rem,3vw,2.2rem));filter:blur(8px);transition:opacity .9s var(--ease),transform .9s var(--ease),filter .9s var(--ease)}
    .visible .reveal{opacity:1;transform:translateY(0);filter:blur(0)}
    .visible .reveal:nth-child(2){transition-delay:.12s}.visible .reveal:nth-child(3){transition-delay:.22s}.visible .reveal:nth-child(4){transition-delay:.32s}

    /* === LAYOUT VARIANTS === */
    .hero-copy{justify-content:flex-end;padding-bottom:clamp(2rem,6vh,5rem)}
    .split{display:grid;grid-template-columns:1.05fr .95fr;align-items:end;gap:clamp(1.3rem,4vw,4rem)}
    .copy-pane{max-width:min(48vw,740px)}
    .editorial .copy-pane h2{font-size:clamp(1.9rem,4.9vw,4.8rem);max-width:13.5ch}
    .editorial .copy-pane p{margin-top:clamp(.75rem,1.5vh,1rem);max-width:42ch}
    .gap-stack{display:grid;gap:clamp(.7rem,1.5vh,1.1rem);align-self:center}
    .gap-card{border-top:1px solid var(--line);padding-top:clamp(.65rem,1.2vh,1rem)}
    .gap-card b{display:block;font-family:var(--display);font-size:clamp(1.15rem,2vw,1.9rem);line-height:1.02;margin-bottom:clamp(.25rem,.8vh,.45rem)}
    .gap-card span{display:block;font-size:clamp(.92rem,1.35vw,1.2rem);line-height:1.34;color:var(--ink-2);max-width:38ch}
    .right-copy{margin-left:auto;max-width:min(43vw,620px);justify-content:center}
    .image-left .right-copy{max-width:min(49vw,720px)}
    .image-left .right-copy h2{font-size:clamp(2rem,5vw,4.8rem);max-width:12.5ch}
    .image-left .right-copy p{max-width:38ch}
    .left-copy{max-width:min(43vw,620px);justify-content:center}
    .center-copy{align-items:center;text-align:center;justify-content:center}
    .center-copy p{margin-inline:auto}
    .massive{font-size:clamp(3rem,10vw,9.8rem);max-width:12ch}
    .massive span{color:inherit}
    .line-note{margin-top:clamp(1rem,2vh,1.4rem)}
    .three-words{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(.7rem,2vw,2rem);width:100%;align-items:stretch;margin-top:clamp(1.1rem,4vh,2.6rem)}
    .word-card{border-top:1px solid var(--line);padding-top:clamp(.85rem,2vh,1.4rem)}
    .word-card h3{font-size:clamp(1.7rem,4.5vw,4.4rem);line-height:.9;margin-bottom:clamp(.7rem,1.2vh,1rem)}
    .word-card p{font-size:clamp(.85rem,1.25vw,1.15rem);line-height:1.36;color:var(--ink-2);max-width:24ch}
    .meaning-center h2{font-size:clamp(2.4rem,7vw,6.7rem);max-width:11ch}
    .meaning-copy{width:min(72vw,880px);margin-top:clamp(1rem,3vh,2rem)}
    .meaning-copy p{background:var(--paper);border:1px solid var(--line);padding:clamp(.95rem,1.8vw,1.35rem);font-family:var(--display);font-weight:700;font-size:clamp(1.1rem,2.1vw,2rem);line-height:1.08;color:var(--ink);max-width:none}
    .flow .slide-content{justify-content:center}
    .flow h2{font-size:clamp(2rem,5vw,4.8rem);max-width:18ch}
    .flow-line{display:grid;grid-template-columns:repeat(4,1fr);gap:clamp(.55rem,1vw,.9rem);width:100%;margin-top:clamp(1.1rem,4vh,2.6rem)}
    .step{min-height:clamp(8rem,23vh,13rem);background:var(--paper);border:1px solid var(--line);padding:clamp(.78rem,1.25vw,1.15rem);display:grid;align-content:start}
    .step b{font-size:clamp(1rem,1.8vw,1.55rem);color:var(--lilac-dark);grid-row:1 / span 2}
    .step span{font-family:var(--display);font-size:clamp(1rem,1.75vw,1.6rem);font-weight:700;line-height:.98;margin-top:clamp(.35rem,.7vh,.5rem)}
    .step p{font-size:clamp(.76rem,1vw,.95rem);line-height:1.3;margin-top:clamp(.35rem,.8vh,.55rem);color:var(--ink-2);max-width:28ch}
    .phase-grid{display:grid;grid-template-columns:.85fr 1.15fr;align-items:end;gap:clamp(1rem,4vw,4rem)}
    .phase-grid > div:first-child p:not(.phase){margin-top:clamp(.8rem,1.4vh,1.1rem);max-width:34ch}
    .tile-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:clamp(.6rem,1.5vw,1.2rem)}
    .tile,.media{background:rgba(250,248,244,.86);border:1px solid rgba(22,21,20,.12);padding:clamp(.85rem,1.7vw,1.35rem)}
    .tile b,.media b{display:block;font-family:var(--display);font-size:clamp(1.05rem,1.9vw,1.75rem);line-height:1;font-weight:700;margin-bottom:clamp(.35rem,.8vh,.55rem)}
    .tile span,.media span{display:block;font-size:clamp(.78rem,1.08vw,1rem);line-height:1.32;color:var(--ink-2);max-width:29ch}
    .takeover-layout{display:grid;grid-template-columns:.9fr 1fr;align-items:center;gap:clamp(1rem,5vw,5rem)}
    .takeover-copy h2{max-width:9ch}.takeover-copy p{color:var(--line)}
    .billboard{background:var(--paper);color:var(--ink);padding:clamp(1rem,3vw,2.5rem);min-height:min(56vh,460px);display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 2rem 5rem rgba(0,0,0,.3)}
    .billboard img{width:clamp(6rem,12vw,10rem);max-height:none}.billboard h3{font-size:clamp(2.3rem,5vw,5rem);line-height:.95}.billboard p{color:var(--ink-2)}
    .portrait-card{justify-self:end;width:min(36vw,430px);background:var(--paper);padding:clamp(.6rem,1vw,1rem);border:1px solid var(--line)}
    .photo-card{height:min(52vh,430px);background-image:var(--img);background-size:cover;background-position:center 34%;margin-bottom:clamp(.6rem,1vh,.9rem)}
    .portrait-card span{font-family:var(--body);font-size:var(--small-size);text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
    .media-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(.6rem,1.2vw,1rem);width:min(100%,1040px);margin-top:clamp(1rem,4vh,2.5rem)}
    .awareness h2{max-width:14ch}
    .awareness p{max-width:60ch}
    .sustain-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(.65rem,1vw,.9rem);margin-top:clamp(1rem,3vh,1.8rem);width:min(44vw,650px)}
    .sustain-list span{background:rgba(250,248,244,.88);border:1px solid var(--line);padding:clamp(.8rem,1.5vw,1.1rem);font-family:var(--display);font-size:clamp(1rem,1.7vw,1.55rem);font-weight:700;line-height:1.05}

    /* === NAVIGATION === */
    .progress{position:fixed;left:0;top:0;height:3px;background:linear-gradient(90deg,#6E3FA8,#B8A3D6,#E36BA4);width:0;z-index:20}
    .nav-dots{position:fixed;right:clamp(.7rem,1.5vw,1.2rem);top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:.5rem;z-index:20}
    .nav-dot{width:.45rem;height:.45rem;border-radius:50%;border:1px solid rgba(122,91,168,.55);background:transparent;cursor:pointer}
    .nav-dot.active{background:var(--lilac-dark)}

    /* === RESPONSIVE FITTING === */
    @media (max-width: 760px){
      .split,.phase-grid,.takeover-layout{grid-template-columns:1fr}
      .photo.side,.photo.side.right{position:absolute;inset:0;width:100%;opacity:.24}
      .right-copy,.left-copy,.copy-pane{max-width:92vw;margin:0}
      .three-words,.flow-line,.media-grid{grid-template-columns:1fr}
      .tile-grid{grid-template-columns:1fr}
      .agency-logo{width:clamp(4.8rem,15vw,6rem)}
    }
    @media (max-height:700px){.billboard{min-height:50vh}.photo-card{height:42vh}.step{min-height:7rem}}
    @media (prefers-reduced-motion: reduce){.reveal{filter:none;transform:none}}
  </style>
</head>
<body>
  <div class="progress" id="progress"></div>
  <nav class="nav-dots" id="navDots" aria-label="Slide navigation"></nav>
  ${slides.join("\n")}
  <script>
    /* === SLIDE PRESENTATION CONTROLLER === */
    class SlidePresentation {
      constructor(){
        this.slides=[...document.querySelectorAll('.slide')];
        this.dots=document.getElementById('navDots');
        this.progress=document.getElementById('progress');
        this.current=0;
        this.buildDots();
        this.observe();
        this.bindKeys();
        this.bindWheel();
        this.bindTouch();
        this.go(0);
      }
      buildDots(){
        this.slides.forEach((_,i)=>{
          const b=document.createElement('button');
          b.className='nav-dot'; b.setAttribute('aria-label','Go to slide '+(i+1));
          b.addEventListener('click',()=>this.go(i));
          this.dots.appendChild(b);
        });
      }
      observe(){
        const io=new IntersectionObserver(entries=>{
          entries.forEach(e=>{
            if(e.isIntersecting){
              const i=this.slides.indexOf(e.target);
              this.current=i;
              this.slides.forEach(s=>s.classList.remove('visible'));
              e.target.classList.add('visible');
              this.update();
            }
          });
        },{threshold:.55});
        this.slides.forEach(s=>io.observe(s));
      }
      bindKeys(){
        window.addEventListener('keydown',e=>{
          if(['ArrowDown','ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();this.go(this.current+1)}
          if(['ArrowUp','ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();this.go(this.current-1)}
          if(e.key==='Home')this.go(0);
          if(e.key==='End')this.go(this.slides.length-1);
        });
      }
      bindWheel(){
        let lock=false;
        window.addEventListener('wheel',e=>{
          if(lock || Math.abs(e.deltaY)<25)return;
          lock=true; this.go(this.current+(e.deltaY>0?1:-1));
          setTimeout(()=>lock=false,650);
        },{passive:true});
      }
      bindTouch(){
        let start=0;
        window.addEventListener('touchstart',e=>start=e.touches[0].clientY,{passive:true});
        window.addEventListener('touchend',e=>{
          const end=e.changedTouches[0].clientY;
          if(Math.abs(start-end)>45)this.go(this.current+(start>end?1:-1));
        },{passive:true});
      }
      go(i){
        const next=Math.max(0,Math.min(this.slides.length-1,i));
        this.slides[next].scrollIntoView({behavior:'smooth',block:'start'});
      }
      update(){
        [...this.dots.children].forEach((d,i)=>d.classList.toggle('active',i===this.current));
        this.progress.style.width=((this.current+1)/this.slides.length*100)+'%';
      }
    }
    new SlidePresentation();
  </script>
</body>
</html>`;

fs.writeFileSync(out, html, "utf8");
console.log(out);
