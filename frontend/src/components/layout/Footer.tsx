const YOUTUBE_URL = 'https://www.youtube.com/@chacha';
const VRL_URL = 'https://www.vrl.co.kr';
const INSTAGRAM_URL = 'https://www.instagram.com/';

export function Footer() {
  return (
    <footer className="py-12 px-6 md:px-12 text-center border-t border-primary/[0.08]">
      <div className="text-[18px] font-bold text-primary mb-4">CHACHA</div>
      <p className="text-[13px] text-muted-foreground">AI 교육 유튜브 채널</p>
      <div className="flex justify-center gap-6 mt-4">
        <a
          href={YOUTUBE_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[13px] text-muted-foreground hover:text-primary transition-colors duration-200"
        >
          YouTube
        </a>
        <a
          href={VRL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[13px] text-muted-foreground hover:text-primary transition-colors duration-200"
        >
          VRL
        </a>
        <a
          href={INSTAGRAM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[13px] text-muted-foreground hover:text-primary transition-colors duration-200"
        >
          Instagram
        </a>
      </div>
      <p className="mt-6 text-[12px] text-muted-foreground opacity-60">
        © 2026 CHACHA. All rights reserved.
      </p>
    </footer>
  );
}
