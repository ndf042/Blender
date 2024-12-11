import bpy
from bpy.props import IntProperty, BoolProperty

#アドオンの情報
bl_info = {
    "name": "ボーンの選択",
    "author": "ndf42",
    "version": (1, 0),
    "blender": (4, 1, 0),
    "location": "3Dビューポート > 選択",
    "description": "ボーンを選択",
    "warning": "",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/ndf042/ndf042",
    "tracker_url": "",
    "category": "Object"
}


#モードごとに選択方法を変更する
def select_mode(context):
    if context.mode == "OBJECT":
        select_obj = context.selected_objects
    elif context.mode == "EDIT_ARMATURE":
        select_obj = context.selected_editable_bones
    elif context.mode == "POSE":
        select_obj = context.selected_pose_bones
    else:
        return None
    return select_obj


#選択したボーンをリストに読み込む
def obj_setting(context):
    select_obj = select_mode(context)

    objects = []
    for o in select_obj:
        objects.append(o)
    #
    return objects


#モードごとに親の選択方法を変更する
def parent_mode(context, obj):
    if bpy.context.mode == "OBJECT":
        obj.select_set(True)
    elif bpy.context.mode == "EDIT_ARMATURE":
        obj.select = True
    elif bpy.context.mode == "POSE":
        obj.bone.select = True


#モードごとに子の選択方法を変更する
def children_mode(context, obj):
    if context.mode == "OBJECT":
        obj.select_set(True)

    elif context.mode == "EDIT_ARMATURE":
        obj.select = True
        obj.select_head = True
        obj.select_tail = True

    elif context.mode == "POSE":
        obj.bone.select = True
        obj.bone.select_head = True
        obj.bone.select_tail = True


#全て選択
class Select_OT_Full_Bone(bpy.types.Operator):
    bl_idname = "select.full_bone"
    bl_label = "全て選択"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.select_all(action="SELECT")
        elif context.mode == "EDIT_ARMATURE":
            bpy.ops.armature.select_all(action="SELECT")
        elif context.mode == "POSE":
            bpy.ops.pose.select_all(action="SELECT")
        return {"FINISHED"}


#アイランド選択
class Select_OT_Island_Bone(bpy.types.Operator):
    bl_idname = "select.island_bone"
    bl_label = "アイランド選択"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        select_obj = select_mode(context)

        if select_obj:
            #最初に選択したボーンを記憶
            first_objects = obj_setting(context)
            #関数用の入力値を用意
            objects = first_objects

            #最初に選択したボーンそれぞれの最上層のボーンを記憶するためのスペース
            root_objects =[]

            for obj in objects:
                #選択したボーンがアイランド選択できない場合に警告文を表示
                if not obj.parent and not obj.children:
                    self.report({"WARNING"}, "一部に選択するボーンが存在しませんでした")

                #選択したボーンの最上層のボーンに遡る
                while obj.parent:
                    obj = obj.parent

                #最上層のボーンを記憶
                root_objects.append(obj)

                #選択しながら最下層のボーンまで下る関数
                def select_island(obj):
                    parent_mode(context, obj)

                    for child in obj.children:
                        select_island(child)

            #最上層から最下層までボーンを選択していく
            for root_obj in root_objects:
                select_island(root_obj)

        else:
            self.report({"ERROR"}, "ボーンが選択されていません")
            return{"CANCELLED"}
        
        return {"FINISHED"}


#ルート選択
class Select_OT_Route_Bone(bpy.types.Operator):
    bl_idname = "select.route_bone"
    bl_label = "ルート選択"
    bl_options = {"REGISTER", "UNDO"}

    count = 0

    Input_count: IntProperty(
        name="選択範囲",
        description="",
        default=1,
        min=1
    )

    Check_box: BoolProperty(
        name="ルートを全選択",
        description="",
        default=True
    )

    def invoke(self, context, event):
        self.Input_count = 0
        self.Check_box = True
        return self.execute(context)

    def execute(self, context):
        select_obj = select_mode(context)

        if select_obj:
            first_objects = obj_setting(context)
            objects = first_objects

            for obj in objects:

                if not obj.parent and not obj.children:
                    self.report({"WARNING"}, "一部に選択するボーンが存在しませんでした")

                def select_parent(obj, count):
                    if self.Check_box == True:
                        if obj.parent:
                            obj = obj.parent

                            parent_mode(context, obj)
                            
                            select_parent(obj, count)

                    else:
                        if count < self.Input_count and obj.parent:
                            obj = obj.parent

                            parent_mode(context, obj)
                            
                            select_parent(obj, count+1)

                def select_children(obj, count):
                    if self.Check_box == True:
                        children_mode(context, obj)

                        if not obj.children:
                            return
                            
                        for child in obj.children:
                            select_children(child, count)
                            
                    else:
                        children_mode(context, obj)

                        if count >= self.Input_count or not obj.children:
                            return

                        for child in obj.children:
                            select_children(child, count+1)

            for first_obj in first_objects:
                select_parent(first_obj, self.count)
                select_children(first_obj, self.count)
        
        else:
            self.report({"ERROR"}, "ボーンが選択されていません")
            return{"CANCELLED"}

        return {"FINISHED"}


#子選択
class Select_OT_Route_Children(bpy.types.Operator):
    bl_idname = "select.route_children"
    bl_label = "子選択"
    bl_options = {"REGISTER", "UNDO"}

    count = 0
    
    Input_count: IntProperty(
        name="選択範囲",
        description="",
        default=1,
        min=1
    )

    Check_box: BoolProperty(
        name="子を全選択",
        description="",
        default=True
    )

    def invoke(self, context, event):
            self.Input_count = 0
            self.Check_box = True
            return self.execute(context)
    
    def execute(self, context):
        select_obj = select_mode(context)

        if select_obj:
            first_objects = obj_setting(context)
            objects = first_objects

            for obj in objects:
                if not obj.children:
                    self.report({"WARNING"}, "一部に選択するボーンが存在しませんでした")

                def select_children(obj, count):
                    if self.Check_box == True:
                        children_mode(context, obj)

                        if not obj.children:
                            return
                            
                        for child in obj.children:
                            select_children(child, count)
                            
                    else:
                        children_mode(context, obj)

                        if count >= self.Input_count or not obj.children:
                            return

                        for child in obj.children:
                            select_children(child, count+1)

            for first_obj in first_objects:
                select_children(first_obj, self.count)
        
        else:
            self.report({"ERROR"}, "ボーンが選択されていません")
            return{"CANCELLED"}

        return {"FINISHED"}
   

#親選択
class Select_OT_Route_Parent(bpy.types.Operator):
    bl_idname = "select.route_parent"
    bl_label = "親選択"
    bl_options = {"REGISTER", "UNDO"}

    count = 0

    Input_count: IntProperty(
        name="選択範囲",
        description="",
        default=1,
        min=1
    )

    Check_box: BoolProperty(
        name="親を全選択",
        description="",
        default=True
    )

    def invoke(self, context, event):
        self.Input_count = 0
        self.Check_box = True
        return self.execute(context)

    def execute(self, context):
        select_obj = select_mode(context)
        
        if select_obj:
            first_objects = obj_setting(context)
            objects = first_objects

            for obj in objects:
                if not obj.parent:
                    self.report({"WARNING"}, "一部に選択するボーンが存在しませんでした")

                def select_parent(obj, count):
                    if self.Check_box == True:
                        if obj.parent:
                            obj = obj.parent

                            parent_mode(context, obj)
                            
                            select_parent(obj, count)

                    else:
                        if count < self.Input_count and obj.parent:
                            obj = obj.parent

                            parent_mode(context, obj)
                            
                            select_parent(obj, count+1)

            for first_obj in first_objects:
                select_parent(first_obj, self.count)

        else:
            self.report({"ERROR"}, "ボーンが選択されていません")
            return{"CANCELLED"}

        return {"FINISHED"}
  

#サブメニューに配置
class Select_PT_Panel_List(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Select"
    bl_label = "ボーン選択"


    @classmethod
    def poll(cls, context):
        for o in bpy.data.objects:
            if o.select_get():
                return(True)
        return({"FINISHED"})
    
    def draw(self,context):
        layout = self.layout

        select_obj = select_mode(context)
        
        if context.mode == "OBJECT":
            layout.label(text="オブジェクトモード")
        elif context.mode == "EDIT_ARMATURE":
            layout.label(text="編集モード")
        elif context.mode == "POSE":
            layout.label(text="ポーズモード")

        layout.operator(Select_OT_Full_Bone.bl_idname, text = "{}".format(Select_OT_Full_Bone.bl_label))

        if select_obj:
            layout.separator()
            layout.operator(Select_OT_Island_Bone.bl_idname, text = "{}".format(Select_OT_Island_Bone.bl_label))
            layout.separator()
            layout.operator(Select_OT_Route_Bone.bl_idname, text = "{}".format(Select_OT_Route_Bone.bl_label))
            
            row = layout.row()
            box = row.box()
            box_row = box.row()
            box_column = box_row.column()

            box_column.operator(Select_OT_Route_Children.bl_idname, text = "{}".format(Select_OT_Route_Children.bl_label))
            box_column = box_row.column()
            box_column.operator(Select_OT_Route_Parent.bl_idname, text = "{}".format(Select_OT_Route_Parent.bl_label))


classes = [
    Select_OT_Full_Bone,
    Select_OT_Island_Bone,
    Select_OT_Route_Bone,
    Select_OT_Route_Children,
    Select_OT_Route_Parent,
    Select_PT_Panel_List
]


#メニューに配置
def menu_func(self, context):
    for c in classes:
        self.layout.operator(c.bl_idname)


addon_shortcut = {
    Select_OT_Full_Bone:"U",
    Select_OT_Island_Bone:"Y",
    Select_OT_Route_Bone:"T",
    Select_OT_Route_Children:"R",
    Select_OT_Route_Parent:"E"
}
addon_keymaps = []


#ショートカットキーの配置
def register_shortcut():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    kmi_list = []
    if kc:
        km = kc.keymaps.new(
            name = "3D View",
            space_type = "VIEW_3D"
            )
        for key, value in addon_shortcut.items():
            kmi = km.keymap_items.new(
                idname=key.bl_idname,
                type=value,
                value="PRESS",
                shift=False,
                ctrl=True,
                alt=True

            )

            kmi_list.append(kmi)
        
        for k in kmi_list:
            addon_keymaps.append((km, k))

        
#ショートカットキーの削除
def unregister_shortcut():
    for km, kmi_list in addon_keymaps:
        km.keymap_items.remove(kmi_list)
    
    addon_keymaps.clear()


addon_name = bl_info["name"]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_select_object.append(menu_func)
    bpy.types.VIEW3D_MT_select_edit_armature.append(menu_func)
    bpy.types.VIEW3D_MT_select_pose.append(menu_func)
    register_shortcut()


def unregister():
    unregister_shortcut()
    bpy.types.VIEW3D_MT_select_pose.remove(menu_func)
    bpy.types.VIEW3D_MT_select_edit_armature.remove(menu_func)
    bpy.types.VIEW3D_MT_select_object.remove(menu_func)
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
