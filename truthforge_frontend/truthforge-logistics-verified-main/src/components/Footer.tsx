import { Link } from 'react-router-dom';
import logo from '@/assets/truthforge-logo.png';

const Footer = () => {
  return (
    <footer className="w-full bg-[hsl(213,70%,10%)] border-t border-[hsl(213,40%,25%)] mt-auto">
      <div className="container mx-auto px-4 py-8 md:py-12">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12 mb-8">
          {/* Left Section - Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <img src={logo} alt="TruthForge" className="h-7 w-7 object-contain" />
              <span className="text-xl font-heading font-bold text-[hsl(210,20%,90%)]">
                TruthForge
              </span>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold text-[hsl(210,20%,85%)] leading-relaxed">
                The Verifiable Intelligence Layer for Global Trade
              </p>
              <p className="text-xs text-[hsl(210,20%,60%)] leading-relaxed">
                AI-powered verification for global supply chain operations
              </p>
            </div>
          </div>

          {/* Middle Section - Platform */}
          <div className="space-y-4">
            <h3 className="text-sm font-heading font-bold text-[hsl(210,20%,90%)] uppercase tracking-wider">
              Platform
            </h3>
            <ul className="space-y-2">
              <li>
                <Link
                  to="/public"
                  className="text-sm text-[hsl(210,20%,70%)] hover:text-[hsl(190,100%,50%)] transition-colors"
                >
                  Dashboard
                </Link>
              </li>
              <li>
                <Link
                  to="/public"
                  className="text-sm text-[hsl(210,20%,70%)] hover:text-[hsl(190,100%,50%)] transition-colors"
                >
                  Port Operations
                </Link>
              </li>
              <li>
                <Link
                  to="/public"
                  className="text-sm text-[hsl(210,20%,70%)] hover:text-[hsl(190,100%,50%)] transition-colors"
                >
                  Supply Chain Intelligence
                </Link>
              </li>
            </ul>
          </div>

          {/* Right Section - Resources */}
          <div className="space-y-4">
            <h3 className="text-sm font-heading font-bold text-[hsl(210,20%,90%)] uppercase tracking-wider">
              Resources
            </h3>
            <ul className="space-y-2">
              <li>
                <a
                  href="#"
                  className="text-sm text-[hsl(210,20%,70%)] hover:text-[hsl(190,100%,50%)] transition-colors"
                  onClick={(e) => e.preventDefault()}
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-[hsl(210,20%,70%)] hover:text-[hsl(190,100%,50%)] transition-colors"
                  onClick={(e) => e.preventDefault()}
                >
                  Privacy
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Line */}
        <div className="pt-6 border-t border-[hsl(213,40%,20%)]">
          <p className="text-xs text-[hsl(210,20%,55%)] text-center">
            © 2026 TruthForge. Built on Hedera.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
