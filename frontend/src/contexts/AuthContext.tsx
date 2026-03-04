"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, User, signOut as firebaseSignOut } from "firebase/auth";
import { auth, db } from "@/lib/firebase";
import { doc, onSnapshot, setDoc, getDoc } from "firebase/firestore";
import { useRouter } from "next/navigation";

interface AuthContextType {
    user: User | null;
    loading: boolean;
    credits: number | undefined;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    credits: undefined,
    signOut: async () => { },
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [credits, setCredits] = useState<number | undefined>(undefined);
    const router = useRouter();

    useEffect(() => {
        let unsubscribeCredits: () => void;

        const unsubscribeAuth = onAuthStateChanged(auth, async (currentUser) => {
            setUser(currentUser);
            setLoading(false);

            // Sync Credits
            if (currentUser) {
                const userDocRef = doc(db, "users", currentUser.uid);

                // Bulletproof fallback: Ensure doc exists on auth
                const docSnap = await getDoc(userDocRef);
                if (!docSnap.exists()) {
                    await setDoc(userDocRef, { creditBalanceMinutes: 10 });
                }

                unsubscribeCredits = onSnapshot(userDocRef, (doc) => {
                    if (doc.exists()) {
                        setCredits(doc.data().creditBalanceMinutes);
                    }
                });
            } else {
                setCredits(undefined);
                if (unsubscribeCredits) unsubscribeCredits();
            }
        });

        return () => {
            unsubscribeAuth();
            if (unsubscribeCredits) unsubscribeCredits();
        };
    }, []);

    const signOut = async () => {
        await firebaseSignOut(auth);
        router.push("/");
    };

    // TEST MODE OVERRIDE: Give local developers unlimited credits for testing UI
    const displayCredits =
        process.env.NODE_ENV === "development" && credits !== undefined && credits < 1000
            ? 1000
            : credits;

    return (
        <AuthContext.Provider value={{ user, loading, credits: displayCredits, signOut }}>
            {children}
        </AuthContext.Provider>
    );
};
