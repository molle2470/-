const YOUTUBE_URL = 'https://www.youtube.com/@chacha';

export function HeroSection() {
  return (
    <section className="min-h-screen flex items-center justify-center px-6 md:px-12 pt-[120px] pb-20 relative overflow-hidden">
      {/* Background decorations */}
      <div
        className="absolute -top-[200px] -right-[200px] w-[600px] h-[600px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(85,140,140,0.06) 0%, transparent 70%)' }}
      />
      <div
        className="absolute -bottom-[100px] -left-[100px] w-[400px] h-[400px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(239,247,255,0.8) 0%, transparent 70%)' }}
      />

      <div className="max-w-[800px] text-center relative z-[1]">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-[#EFF7FF] border border-[#D8E8E8] px-5 py-2 rounded-full text-[13px] font-semibold text-primary mb-8 animate-[fadeUp_0.8s_ease_both]">
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          AI 교육 유튜브 채널
        </div>

        {/* Headline */}
        <h1 className="text-[clamp(40px,6vw,64px)] font-bold leading-[1.15] tracking-[-0.04em] text-foreground mb-6 animate-[fadeUp_0.8s_0.1s_ease_both]">
          AI로{' '}
          <span className="text-primary relative inline-block">
            10배
            <span className="absolute bottom-1 left-0 right-0 h-3 bg-primary/[0.12] rounded-[4px] -z-[1]" />
          </span>{' '}
          생산성,
          <br />
          직접 보여드립니다
        </h1>

        {/* Description */}
        <p className="text-[18px] leading-[1.7] text-muted-foreground max-w-[560px] mx-auto mb-10 animate-[fadeUp_0.8s_0.2s_ease_both]">
          바이브코딩, Claude Code, AI 자동화까지.
          <br />
          비개발자도 할 수 있는 AI 활용법을 매주 공유합니다.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-[fadeUp_0.8s_0.3s_ease_both]">
          <a
            href={YOUTUBE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2.5 bg-primary text-white px-9 py-4 rounded-full font-semibold text-[16px] hover:bg-primary-dark hover:-translate-y-0.5 hover:shadow-[0_8px_30px_rgba(85,140,140,0.3)] transition-all duration-300"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
            </svg>
            YouTube 채널 보기
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>
          <a
            href="#content"
            className="inline-flex items-center gap-2 bg-transparent text-foreground px-8 py-4 rounded-full font-medium text-[16px] border border-[#D8E8E8] hover:border-primary hover:text-primary hover:bg-[#EFF7FF] transition-all duration-300"
          >
            어떤 콘텐츠가 있나요?
          </a>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-center gap-8 sm:gap-12 mt-16 pt-12 border-t border-primary/10 animate-[fadeUp_0.8s_0.4s_ease_both]">
          <div className="text-center">
            <div className="text-[32px] font-bold text-primary tracking-[-0.03em]">AI</div>
            <div className="text-[13px] text-muted-foreground mt-1">교육 전문 채널</div>
          </div>
          <div className="text-center">
            <div className="text-[32px] font-bold text-primary tracking-[-0.03em]">Daily</div>
            <div className="text-[13px] text-muted-foreground mt-1">매일 새 영상 업로드</div>
          </div>
          <div className="text-center">
            <div className="text-[32px] font-bold text-primary tracking-[-0.03em]">10x</div>
            <div className="text-[13px] text-muted-foreground mt-1">생산성 향상 목표</div>
          </div>
        </div>
      </div>
    </section>
  );
}
