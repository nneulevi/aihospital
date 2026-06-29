package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.DrugStockRecord;
import com.neuedu.his.model.vo.DrugStockRecordVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface DrugStockRecordMapper {

    @Insert("INSERT INTO drug_stock_record(drug_id, record_type, quantity, before_stock, after_stock, operator_id, related_prescription_id, reason) " +
            "VALUES(#{drugId}, #{recordType}, #{quantity}, #{beforeStock}, #{afterStock}, #{operatorId}, #{relatedPrescriptionId}, #{reason})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DrugStockRecord record);

    List<DrugStockRecordVO> selectByCondition(@Param("drugId") Integer drugId,
                                              @Param("recordType") String recordType);
}
