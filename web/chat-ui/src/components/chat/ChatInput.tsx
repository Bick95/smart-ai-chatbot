"use client"

import * as React from "react"
import { useForm } from "@tanstack/react-form"
import * as z from "zod"

import {
  InputGroup,
  InputGroupAddon,
  InputGroupTextarea,
  InputGroupButton,
} from "@/components/ui/input-group"
import { Send } from "lucide-react"

const formSchema = z.object({
  message: z
    .string()
    .min(1, "Message cannot be empty")
    .max(65_536, "Message is too long"),
})

export interface ChatInputProps {
  onSubmit: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSubmit,
  disabled = false,
  placeholder = "Message ChatGPT...",
}: ChatInputProps) {
  const form = useForm({
    defaultValues: {
      message: "",
    },
    validators: {
      onSubmit: formSchema,
    },
    onSubmit: async ({ value }) => {
      onSubmit(value.message)
      form.reset()
    },
  })

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      form.handleSubmit()
    }
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        form.handleSubmit()
      }}
      className="w-full"
    >
      <form.Field
        name="message"
        children={(field) => (
          <InputGroup className="min-h-12 has-[>textarea]:min-h-12 has-[>textarea]:py-3">
            <InputGroupTextarea
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(e) => field.handleChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              rows={1}
              className="max-h-48 min-h-12 resize-none py-3"
              disabled={disabled}
              aria-label="Message"
            />
            <InputGroupAddon align="inline-end">
              <InputGroupButton
                type="submit"
                size="icon-sm"
                disabled={disabled || !field.state.value.trim()}
                aria-label="Send message"
              >
                <Send className="size-4" />
              </InputGroupButton>
            </InputGroupAddon>
          </InputGroup>
        )}
      />
    </form>
  )
}
