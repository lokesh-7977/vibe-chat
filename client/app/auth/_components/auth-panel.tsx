"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCheck,
  LockKeyhole,
  Mail,
  MessageCircle,
  Sparkles,
  UserRound,
} from "lucide-react";

import { loginUser, registerUser } from "../../../apis/auth";
import {
  getFieldErrors,
  loginSchema,
  type LoginValues,
  registerSchema,
  type RegisterValues,
} from "../../../schemas";
import { useAppDispatch } from "../../../store/hooks";
import { setAuth } from "../../../store/slices/auth-slice";
import { useToast } from "@/providers/toast-provider";
import type { ApiResponse, AuthTokensResponse } from "../../../types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldContent,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldSet,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type AuthTab = "login" | "register";
type LoginErrors = Partial<Record<keyof LoginValues, string>>;
type RegisterErrors = Partial<Record<keyof RegisterValues, string>>;

const initialLoginForm: LoginValues = {
  email: "",
  password: "",
};

const initialRegisterForm: RegisterValues = {
  fullName: "",
  email: "",
  password: "",
};

export default function AuthPanel() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [activeTab, setActiveTab] = useState<AuthTab>("login");
  const [loginForm, setLoginForm] = useState(initialLoginForm);
  const [registerForm, setRegisterForm] = useState(initialRegisterForm);
  const [loginErrors, setLoginErrors] = useState<LoginErrors>({});
  const [registerErrors, setRegisterErrors] = useState<RegisterErrors>({});
  const { toast } = useToast();

  const registerMutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (data) => {
      setRegisterErrors({});
      setRegisterForm(initialRegisterForm);
      const result = data as ApiResponse<AuthTokensResponse>;
      if (result.data) {
        dispatch(
          setAuth({
            accessToken: result.data.accessToken,
            user: result.data.user,
          }),
        );
        router.replace("/chats");
      }
    },
    onError: (error) => {
      const err = error as { response?: { data?: { message?: string } } };
      const message =
        err.response?.data?.message ??
        (error instanceof Error ? error.message : "Please try again.");
      toast({
        title: "Registration failed",
        description: message,
        kind: "error",
      });
    },
  });

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      setLoginErrors({});
      const result = data as ApiResponse<AuthTokensResponse>;
      if (result.data) {
        dispatch(
          setAuth({
            accessToken: result.data.accessToken,
            user: result.data.user,
          }),
        );
        router.replace("/chats");
      }
    },
    onError: (error) => {
      const err = error as { response?: { data?: { message?: string } } };
      const message =
        err.response?.data?.message ??
        (error instanceof Error ? error.message : "Please try again.");
      toast({ title: "Login failed", description: message, kind: "error" });
    },
  });

  const isSubmitting = registerMutation.isPending || loginMutation.isPending;

  function submitLogin() {
    const result = loginSchema.safeParse(loginForm);

    if (!result.success) {
      setLoginErrors(getFieldErrors(result.error));
      return;
    }

    setLoginErrors({});
    loginMutation.mutate(result.data);
  }

  function submitRegister() {
    const result = registerSchema.safeParse(registerForm);

    if (!result.success) {
      setRegisterErrors(getFieldErrors(result.error));
      return;
    }

    setRegisterErrors({});
    registerMutation.mutate(result.data);
  }

  return (
    <main className="flex min-h-screen flex-1 items-center justify-center overflow-hidden bg-whatsapp-surface px-4 py-4 text-foreground sm:px-6 lg:px-8">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-lg border border-whatsapp-border bg-card shadow-lg shadow-whatsapp-deep/10 lg:grid-cols-2">
        <section className="relative hidden overflow-hidden bg-whatsapp-deep p-8 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute right-8 top-8 size-24 rounded-full border border-white/10 bg-white/5" />
          <div className="absolute bottom-16 right-16 size-16 rounded-full border border-white/10 bg-white/5" />

          <div className="relative">
            <div className="flex size-12 items-center justify-center rounded-lg bg-whatsapp text-whatsapp-foreground shadow-md shadow-black/10">
              <MessageCircle className="size-6" />
            </div>
            <div className="mt-7 max-w-md">
              <p className="text-sm font-medium uppercase tracking-normal text-white/70">
                Aura Chat
              </p>
              <h1 className="mt-3 text-3xl font-semibold leading-tight">
                Sign in to your workspace with a calmer chat experience.
              </h1>
              <p className="mt-4 text-sm leading-6 text-white/75">
                Sign in to continue your workspace, channels, files, and
                realtime activity in one calm place.
              </p>
            </div>
          </div>

          <div className="relative space-y-3">
            <div className="ml-auto max-w-sm rounded-lg rounded-br-sm bg-whatsapp-bubble p-4 text-sm text-whatsapp-foreground shadow-sm">
              Your messages, tasks, and shared context stay connected across
              channels.
              <div className="mt-2 flex items-center justify-end gap-1 text-xs">
                <span>10:24</span>
                <CheckCheck className="size-4" />
              </div>
            </div>
            <div className="max-w-xs rounded-lg rounded-bl-sm bg-white/10 p-4 text-sm text-white backdrop-blur">
              Pick up every conversation right where you left it.
            </div>
          </div>
        </section>

        <Card className="mx-auto w-full max-w-md justify-center rounded-none border-0 py-0 shadow-none ring-0 lg:max-w-none">
          <CardHeader className="px-6 pt-6 text-center sm:px-10 lg:pt-8">
            <div className="mx-auto flex size-12 items-center justify-center rounded-lg bg-whatsapp text-whatsapp-foreground shadow-sm shadow-whatsapp/30 lg:hidden">
              <MessageCircle className="size-5" />
            </div>
            <CardTitle className="mt-3 text-3xl font-semibold">
              Aura Chat
            </CardTitle>
            <CardDescription className="mx-auto max-w-xs">
              Access your chats, workspaces, and realtime updates.
            </CardDescription>
          </CardHeader>

          <CardContent className="px-6 pb-6 sm:px-10 lg:pb-8">
            <Tabs
              value={activeTab}
              onValueChange={(value) => {
                setActiveTab(value as AuthTab);
                setLoginErrors({});
                setRegisterErrors({});
              }}
            >
              <TabsList
                className="grid h-11 w-full grid-cols-2 bg-whatsapp-muted p-1"
                variant="default"
              >
                <TabsTrigger
                  value="login"
                  className="h-full data-active:bg-card data-active:text-whatsapp-deep"
                >
                  Login
                </TabsTrigger>
                <TabsTrigger
                  value="register"
                  className="h-full data-active:bg-card data-active:text-whatsapp-deep"
                >
                  Register
                </TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                <form
                  className="flex h-96 flex-col justify-between"
                  noValidate
                  onSubmit={(event) => {
                    event.preventDefault();
                    submitLogin();
                  }}
                >
                  <FieldSet>
                    <FieldGroup className="gap-3">
                      <Field>
                        <FieldLabel>Email</FieldLabel>
                        <FieldContent className="relative">
                          <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                          <Input
                            className="h-11 border-whatsapp-border bg-whatsapp-surface pl-10 focus-visible:border-whatsapp focus-visible:ring-whatsapp/25"
                            type="email"
                            autoComplete="email"
                            placeholder="you@example.com"
                            value={loginForm.email}
                            aria-invalid={Boolean(loginErrors.email)}
                            onChange={(event) =>
                              setLoginForm((state) => ({
                                ...state,
                                email: event.target.value,
                              }))
                            }
                          />
                        </FieldContent>
                        <div className="min-h-5">
                          <FieldError
                            errors={
                              loginErrors.email
                                ? [{ message: loginErrors.email }]
                                : undefined
                            }
                          />
                        </div>
                      </Field>

                      <Field>
                        <FieldLabel>Password</FieldLabel>
                        <FieldContent className="relative">
                          <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                          <Input
                            className="h-11 border-whatsapp-border bg-whatsapp-surface pl-10 focus-visible:border-whatsapp focus-visible:ring-whatsapp/25"
                            type="password"
                            autoComplete="current-password"
                            placeholder="Enter your password"
                            value={loginForm.password}
                            aria-invalid={Boolean(loginErrors.password)}
                            onChange={(event) =>
                              setLoginForm((state) => ({
                                ...state,
                                password: event.target.value,
                              }))
                            }
                          />
                        </FieldContent>
                        <div className="min-h-5">
                          <FieldError
                            errors={
                              loginErrors.password
                                ? [{ message: loginErrors.password }]
                                : undefined
                            }
                          />
                        </div>
                      </Field>

                      <div className="flex min-h-12 items-center gap-2 rounded-lg border border-whatsapp-border bg-whatsapp-surface p-3 text-sm text-muted-foreground">
                        <Sparkles className="size-4 text-whatsapp-deep" />
                        <span>
                          Jump back into your chats and shared spaces.
                        </span>
                      </div>
                    </FieldGroup>
                  </FieldSet>

                  <Button
                    type="submit"
                    size="lg"
                    className="h-11 w-full bg-whatsapp text-whatsapp-foreground shadow-sm shadow-whatsapp/20 hover:bg-whatsapp/90"
                    disabled={isSubmitting}
                  >
                    {loginMutation.isPending ? "Signing in..." : "Sign in"}
                    <ArrowRight className="size-4" />
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="mt-0">
                <form
                  className="flex h-96 flex-col justify-between"
                  noValidate
                  onSubmit={(event) => {
                    event.preventDefault();
                    submitRegister();
                  }}
                >
                  <FieldSet>
                    <FieldGroup className="gap-3">
                      <Field>
                        <FieldLabel>Full name</FieldLabel>
                        <FieldContent className="relative">
                          <UserRound className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                          <Input
                            className="h-11 border-whatsapp-border bg-whatsapp-surface pl-10 focus-visible:border-whatsapp focus-visible:ring-whatsapp/25"
                            autoComplete="name"
                            placeholder="Your name"
                            value={registerForm.fullName}
                            aria-invalid={Boolean(registerErrors.fullName)}
                            onChange={(event) =>
                              setRegisterForm((state) => ({
                                ...state,
                                fullName: event.target.value,
                              }))
                            }
                          />
                        </FieldContent>
                        <div className="min-h-5">
                          <FieldError
                            errors={
                              registerErrors.fullName
                                ? [{ message: registerErrors.fullName }]
                                : undefined
                            }
                          />
                        </div>
                      </Field>

                      <Field>
                        <FieldLabel>Email</FieldLabel>
                        <FieldContent className="relative">
                          <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                          <Input
                            className="h-11 border-whatsapp-border bg-whatsapp-surface pl-10 focus-visible:border-whatsapp focus-visible:ring-whatsapp/25"
                            type="email"
                            autoComplete="email"
                            placeholder="you@example.com"
                            value={registerForm.email}
                            aria-invalid={Boolean(registerErrors.email)}
                            onChange={(event) =>
                              setRegisterForm((state) => ({
                                ...state,
                                email: event.target.value,
                              }))
                            }
                          />
                        </FieldContent>
                        <div className="min-h-5">
                          <FieldError
                            errors={
                              registerErrors.email
                                ? [{ message: registerErrors.email }]
                                : undefined
                            }
                          />
                        </div>
                      </Field>

                      <Field>
                        <FieldLabel>Password</FieldLabel>
                        <FieldContent className="relative">
                          <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                          <Input
                            className="h-11 border-whatsapp-border bg-whatsapp-surface pl-10 focus-visible:border-whatsapp focus-visible:ring-whatsapp/25"
                            type="password"
                            autoComplete="new-password"
                            placeholder="At least 6 characters"
                            value={registerForm.password}
                            aria-invalid={Boolean(registerErrors.password)}
                            onChange={(event) =>
                              setRegisterForm((state) => ({
                                ...state,
                                password: event.target.value,
                              }))
                            }
                          />
                        </FieldContent>
                        <div className="min-h-5">
                          <FieldError
                            errors={
                              registerErrors.password
                                ? [{ message: registerErrors.password }]
                                : undefined
                            }
                          />
                        </div>
                      </Field>
                    </FieldGroup>
                  </FieldSet>

                  <Button
                    type="submit"
                    size="lg"
                    className="h-11 w-full bg-whatsapp text-whatsapp-foreground shadow-sm shadow-whatsapp/20 hover:bg-whatsapp/90"
                    disabled={isSubmitting}
                  >
                    {registerMutation.isPending
                      ? "Creating account..."
                      : "Create account"}
                    <ArrowRight className="size-4" />
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
