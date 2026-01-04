import Link from "next/link";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-lg border-b border-gray-200">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="text-xl font-bold text-gray-900 hover:text-purple-600 transition-colors"
          aria-label="NUCTECS Home"
        >
          <span className="text-purple-600">NU</span>CTECS
        </Link>

        <nav aria-label="Primary" className="flex items-center gap-1">
          <Link
            href="/discover"
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
          >
            Discover
          </Link>
          <Link
            href="/search"
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
          >
            Search
          </Link>
          <Link
            href="/signin"
            className="ml-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg border border-purple-600 hover:border-purple-700 transition-all duration-200 shadow-md hover:shadow-lg"
          >
            Sign in
          </Link>
        </nav>
      </div>
    </header>
  );
}

