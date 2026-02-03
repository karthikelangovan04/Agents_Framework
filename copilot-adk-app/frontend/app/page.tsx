"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const redirectedRef = useRef(false);

  useEffect(() => {
    if (loading) return;
    if (redirectedRef.current) return;
    
    redirectedRef.current = true;
    if (user) {
      router.replace("/chat");
    } else {
      router.replace("/login");
    }
  }, [user, loading, router]);

  return (
    <main style={{ padding: "2rem", textAlign: "center" }}>
      <p>Loading...</p>
    </main>
  );
}
