'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import { cn } from '@/lib/utils';

const YOUTUBE_URL = 'https://www.youtube.com/@chacha';

const navLinks = [
  { label: '소개', href: '#about' },
  { label: '콘텐츠', href: '#content' },
  { label: '인기 영상', href: '#videos' },
];

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          setIsScrolled(window.scrollY > 20);
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (href: string) => {
    setIsMobileMenuOpen(false);
    if (href.startsWith('#')) {
      const target = document.querySelector(href);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  };

  return (
    <nav
      className={cn(
        'fixed top-0 left-0 right-0 z-50 h-[72px] flex items-center justify-between px-6 md:px-12',
        'bg-[rgba(250,252,255,0.85)] backdrop-blur-xl border-b border-primary/[0.08]',
        'transition-all duration-300',
        isScrolled && 'shadow-[0_1px_20px_rgba(85,140,140,0.08)]'
      )}
    >
      {/* Logo */}
      <Link href="/" className="text-[22px] font-bold text-primary tracking-[-0.5px]">
        CHACHA
      </Link>

      {/* Desktop nav */}
      <div className="hidden md:flex items-center gap-9">
        {navLinks.map((link) => (
          <button
            key={link.label}
            onClick={() => handleNavClick(link.href)}
            className="text-[14px] font-medium text-muted-foreground hover:text-primary transition-colors duration-200 cursor-pointer"
          >
            {link.label}
          </button>
        ))}
        <a
          href={YOUTUBE_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-primary text-white px-6 py-2.5 rounded-full text-[14px] font-semibold hover:bg-primary-dark transition-all duration-300 hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(85,140,140,0.3)]"
        >
          구독하기 →
        </a>
      </div>

      {/* Mobile toggle */}
      <button
        className="md:hidden p-2 text-gray-900 -mr-1"
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        aria-label={isMobileMenuOpen ? '메뉴 닫기' : '메뉴 열기'}
      >
        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Mobile menu */}
      <div
        className={cn(
          'md:hidden absolute top-[72px] left-0 w-full bg-white border-b border-border shadow-lg',
          'transition-all duration-300 overflow-hidden',
          isMobileMenuOpen ? 'max-h-80 opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="px-6 py-5 flex flex-col gap-1">
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => handleNavClick(link.href)}
              className="text-[15px] text-gray-700 hover:text-primary font-medium py-3.5 transition-colors border-b border-gray-50 last:border-0 text-left"
            >
              {link.label}
            </button>
          ))}
          <div className="pt-4 mt-2">
            <a
              href={YOUTUBE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="block bg-primary text-white px-6 py-3 rounded-full text-[14px] font-semibold text-center hover:bg-primary-dark transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              구독하기 →
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}
