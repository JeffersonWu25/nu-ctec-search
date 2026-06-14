import { NextResponse } from 'next/server';
import { isNorthwesternEmail } from '@/app/lib/auth';
import { createClient } from '@/app/lib/supabase/server';

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const redirectTo = searchParams.get('redirect') || '/';

  if (!code) {
    return NextResponse.redirect(`${origin}/signin`);
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.exchangeCodeForSession(code);

  if (error) {
    return NextResponse.redirect(`${origin}/signin`);
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user?.email || !isNorthwesternEmail(user.email)) {
    await supabase.auth.signOut();
    return NextResponse.redirect(`${origin}/signin`);
  }

  return NextResponse.redirect(`${origin}${redirectTo}`);
}
