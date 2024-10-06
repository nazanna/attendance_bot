async def parse_sheet_name(context):
    subject = context.user_data['subject']
    match subject:
        case 1:
            grade = context.user_data['grade']
            group = context.user_data['group']
            sheet_name = str(grade)+'_'+str(group)
        case 2:
            group = context.user_data['group']
            if group == 7:
                sheet_name='7_баз_прак'
            else:
                sheet_name = '8_9_баз_прак'
        case 3:
            grade = context.user_data['grade']
            group = context.user_data['group']
            sheet_name = str(grade)+'_ол_прак_'+str(group)
        case 4:
            sheet_name = 'Механика'
        case 5:
            sheet_name = 'Преподготовка к IPhO'
    return sheet_name
