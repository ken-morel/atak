pub const EType = enum {
    Template,
    Component,
    String,
    Integer,
    Float,
    Boolean,
    Undefined,
    Null,
};

pub const EValue = union(enum) {
    Template: Template,
    Component: Component,
    String: []const u8,
    Integer: i64,
    Float: f64,
    Boolean: bool,
    Undefined,
    Null,
};

pub const EObject = struct {
    value: EValue,
    pub fn init(value: EValue) EObject {
        return .{
            .value = value,
        };
    }
    pub fn isType(self: EObject, t: EType) bool {
        return t == self.getType();
    }
    pub fn getType(self: *const EObject) ?EType {
        return switch (self.value) {
            .String => EType.String,
            .Integer => EType.Integer,
            .Float => EType.Float,
            .Boolean => EType.Boolean,
            .Undefined => EType.Undefined,
        };
    }
};

const Template = @import("componenttemplate.zig").ComponentTemplate;
const Component = @import("component.zig").Component;
