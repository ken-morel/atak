pub const Efus = struct {
    instructions: std.ArrayList(Instruction),
    allocator: Allocator,

    pub fn init(allocator: Allocator, instructions: std.ArrayList(Instruction)) Efus {
        return .{
            .allocator = allocator,
            .instructions = instructions,
        };
    }

    pub fn eval(self: *const Efus, ctx: EvalContext) !?EObject {
        var val: ?EObject = null;
        for (self.instructions.items) |*instr| {
            val = try instr.eval(ctx);
        }
        return val;
    }
};

pub const Parser = struct {
    index: u32,
    text: []const u8,
    file: []const u8,
    allocator: Allocator,

    pub fn init(allocator: Allocator, file: []const u8, text: []const u8) Parser {
        return .{
            .allocator = allocator,
            .index = 0,
            .text = text,
            .file = file,
        };
    }

    pub fn fromFile(mayallocator: ?Allocator, filename: []const u8) !Parser {
        const allocator = mayallocator orelse std.heap.page_allocator;
        const file = try std.fs.cwd().openFile(filename, .{});
        defer file.close();

        const contents = try file.readToEndAlloc(allocator, std.math.maxInt(usize));
        return Parser.init(
            allocator,
            filename,
            contents,
        );
    }

    pub fn isSymbol(c: u8) bool {
        return 'A' <= c and c <= 'z';
    }
    pub fn isSpace(c: u8) bool {
        return c == ' ' or c == '\t';
    }
    pub fn parse_symbol(self: *Parser) !?[]const u8 {
        const start = self.index;
        while (Parser.isSymbol(self.char())) {
            self.next_inline() catch break;
        }
        return self.slicednbefore(start);
    }
    pub fn slicednbefore(self: *Parser, start: u32) ?[]const u8 {
        if (start != self.index) {
            return self.text[start..self.index];
        } else {
            return null;
        }
    }
    pub fn next_inline(self: *Parser) !void {
        self.index += 1;
        if (self.index >= self.text.len) {
            return EfusError.EndOfFile;
        } else if (self.char() == '\n') {
            return EfusError.EndOfLine;
        }
    }
    pub fn parse_compcall(self: *Parser) !?InstantiateComponent {
        if (try self.parse_symbol()) |templname| {
            if (try self.eol()) {
                return InstantiateComponent.init(
                    self.allocator,
                    templname,
                    null,
                    null,
                    null,
                );
            }
            const alias = try self.parse_compcallalias();
            if (try self.eol()) {
                return InstantiateComponent.init(
                    self.allocator,
                    templname,
                    alias,
                    null,
                    null,
                );
            }
            const arguments = try self.parse_compcallargs();
            if (!try self.eol()) {
                return EfusError.ExtraTokensAfterArguments;
            }
            return InstantiateComponent.init(
                self.allocator,
                templname,
                alias,
                arguments,
                null,
            );
        } else {
            return null;
        }
    }
    fn parse_compcallargs(self: *Parser) !std.ArrayList(InstantiateComponentArgument) {
        var args = std.ArrayList(InstantiateComponentArgument).init(self.allocator);
        loop: while (true) {
            const arg = self.parse_next_key_eq_val() catch |err| {
                switch (err) {
                    EfusError.EndOfLine => break :loop,
                    EfusError.EndOfFile => break :loop,
                    else => return err,
                }
            };
            try args.append(arg.arg);
        }
        return args;
    }
    fn parse_next_key_eq_val(self: *Parser) !struct { name: []const u8, arg: InstantiateComponentArgument } {
        const start = self.index;
        _ = try self.skip_inline_spaces();
        if (try self.parse_symbol()) |name| {
            if (self.char() != '=') {
                return EfusError.ExpectedEqualToAfterParamName;
            }
            try self.next_inline();
            if (try self.parse_next_value()) |value| {
                return .{
                    .name = name,
                    .arg = InstantiateComponentArgument{
                        .key = name,
                        .value = value,
                    },
                };
            } else {
                return EfusError.ExpectedValueAfterEqualTo;
            }
        } else {
            self.index = start;
            return EfusError.ExpectedKeyValue;
        }
    }
    pub fn parse_next_value(self: *Parser) !?EObject {
        return (try self.parse_string() orelse
            try self.parse_int() orelse
            try self.parse_float() orelse
            try self.parse_null() orelse
            try self.parse_undefined() orelse
            try self.parse_boolean() orelse
            null);
    }

    pub fn parse_string(self: *Parser) !?EObject {
        if (self.char() != '"') return null;
        try self.next_inline();

        const start = self.index;
        while (true) {
            if (self.index >= self.text.len or self.char() == '\n') {
                return EfusError.UnterminatedString;
            } else if (self.char() == '"') {
                const str = self.text[start..self.index];
                try self.next_inline();
                return EObject.init(.{ .String = str });
            }
            try self.next_inline();
        }
    }

    pub fn parse_int(self: *Parser) !?EObject {
        const start = self.index;
        var has_digits = false;

        if (self.char() == '+' or self.char() == '-') {
            try self.next_inline();
        }

        while (self.index < self.text.len and std.ascii.isDigit(self.char())) {
            has_digits = true;
            try self.next_inline();
        }

        if (has_digits and (self.index >= self.text.len or self.char() != '.')) {
            const num_str = self.text[start..self.index];
            const integer = try std.fmt.parseInt(i64, num_str, 10);
            return EObject.init(.{ .Integer = integer });
        }

        self.index = start;
        return null;
    }

    pub fn parse_float(self: *Parser) !?EObject {
        const start = self.index;
        var has_digits = false;

        if (self.char() == '+' or self.char() == '-') {
            try self.next_inline();
        }

        while (self.index < self.text.len and std.ascii.isDigit(self.char())) {
            has_digits = true;
            try self.next_inline();
        }

        if (self.index < self.text.len and self.char() == '.') {
            try self.next_inline();

            while (self.index < self.text.len and std.ascii.isDigit(self.char())) {
                has_digits = true;
                try self.next_inline();
            }
        }

        if (has_digits) {
            const num_str = self.text[start..self.index];
            const float = try std.fmt.parseFloat(f64, num_str);
            return EObject.init(.{ .Float = float });
        }

        self.index = start;
        return null;
    }

    pub fn parse_boolean(self: *Parser) !?EObject {
        if (self.index + 3 <= self.text.len and
            self.isnext("true"))
        {
            self.index += 4;
            return EObject.init(.{ .Boolean = true });
        } else if (self.index + 4 <= self.text.len and
            self.isnext("false"))
        {
            self.index += 5;
            return EObject.init(.{ .Boolean = false });
        }
        return null;
    }

    pub fn parse_null(self: *Parser) !?EObject {
        if (self.index + 3 <= self.text.len and
            self.isnext("null"))
        {
            self.index += 4;
            return EObject.init(.Null);
        }
        return null;
    }
    pub fn parse_undefined(self: *Parser) !?EObject {
        if (self.index + 3 <= self.text.len and
            self.isnext("undefined"))
        {
            self.index += 4;
            return EObject.init(.Undefined);
        }
        return null;
    }
    fn skip_inline_spaces(self: *Parser) !u32 {
        const start = self.index;
        while (Parser.isSpace(self.char())) {
            try self.next_inline();
        }
        return self.index - start;
    }
    fn parse_compcallalias(self: *Parser) !?[]const u8 {
        if (try self.eol()) {
            return EfusError.EndOfLine;
        }
        if (self.char() == '&') {
            try self.next_inline();
            return try self.parse_symbol();
        } else {
            return null;
        }
    }
    fn char(self: *Parser) u8 {
        return self.text[self.index];
    }
    fn eol(self: *Parser) !bool {
        const start = self.index;
        while (true) {
            if (self.index >= self.text.len) {
                return EfusError.EndOfFile;
            } else if (self.char() == '\n') {
                self.index += 1;
                return true;
            } else if (Parser.isSpace(self.char())) {
                self.index += 1;
            } else {
                self.index = start;
                return false;
            }
        }
    }
    fn parse_instruction(self: *Parser) !Instruction {
        if (self.char() == '#') {
            return .DoNothing;
        } else if (std.ascii.isAlphabetic(self.char())) {
            const comp = try self.parse_compcall() orelse return EfusError.InvalidCompcall;
            return Instruction{ .InstantiateComponent = comp };
        } else {
            return EfusError.UnexpectedToken;
        }
    }
    fn isnext(self: *Parser, text: []const u8) bool {
        return self.index + text.len < self.text.len and std.mem.eql(
            u8,
            self.text[self.index .. self.index + text.len],
            text,
        );
    }
    pub fn parse_next_line(self: *Parser) !?Instruction {
        while (try self.eol()) {}
        const indent = try self.skip_inline_spaces();
        var instr = try self.parse_instruction();
        instr.setIndent(indent);
        return instr;
    }
    pub fn parse(self: *Parser) !?Efus {
        var instructions = std.ArrayList(Instruction).init(self.allocator);
        loop: while (true) {
            const mayline = self.parse_next_line() catch |err| {
                switch (err) {
                    EfusError.EndOfLine => continue :loop,
                    EfusError.EndOfFile => break :loop,
                    else => return err,
                }
            };
            if (mayline) |line| {
                try instructions.append(line);
            }
        }

        return Efus.init(
            self.allocator,
            instructions,
        );
    }
};

const std = @import("std");
const Allocator = std.mem.Allocator;

const instruction = @import("instruction.zig");
const Instruction = instruction.Instruction;
const InstantiateComponent = instruction.InstantiateComponent;
const InstantiateComponentArgument = instruction.InstantiateComponentArgument;
const EvalContext = instruction.EvalContext;

const namespace = @import("namespace");
const Namespace = namespace.Namespace;

const objs = @import("objects.zig");
const EObject = objs.EObject;
const EValue = objs.EValue;
const EType = objs.EType;

const EfusError = @import("errors.zig").EfusError;

const attributemanager = @import("attributemanager.zig");
const EArguments = attributemanager.EArguments;
const EArgument = attributemanager.EArgument;

const print = std.debug.print;

const component = @import("component.zig");
const Component = component.Component;
